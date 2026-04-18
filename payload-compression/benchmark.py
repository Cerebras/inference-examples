"""Benchmark Cerebras Inference payload compression: plain JSON vs msgpack+gzip.

Measures TTFT (time-to-first-token) and E2E (request sent -> last token) across
10 streaming requests per encoding for a ~64k-token coding-review prompt.

Writes:
- results.png  (grouped bar chart: TTFT and E2E per encoding)
- stdout       (per-run progress + markdown results table)
"""

from __future__ import annotations

import gzip
import json
import os
import statistics
import sys
import time
from dataclasses import dataclass
from typing import Callable

import httpx
import matplotlib.pyplot as plt
import msgpack

API_URL = "https://api.cerebras.ai/v1/chat/completions"
MODEL = "llama-3.1-8b"
NUM_RUNS = 5
OUTPUT_TOKENS = 200
TARGET_INPUT_TOKENS = 20_000
CHARS_PER_TOKEN = 3.5  # conservative estimate; we overshoot slightly
MAX_DECOMPRESSED_BYTES = 40 * 1024 * 1024  # 40MB guardrail; server cap is 51MB

# A realistic-looking code block we repeat to build the ~64k-token prompt.
# Same bytes every run => identical server-side KV cache state across encodings.
CODE_BLOCK = '''\
class RequestContext:
    def __init__(self, request_id: str, user_id: str, tenant: str):
        self.request_id = request_id
        self.user_id = user_id
        self.tenant = tenant
        self.started_at = time.perf_counter()
        self._spans: list[Span] = []

    def span(self, name: str) -> "Span":
        span = Span(name=name, parent=self.request_id)
        self._spans.append(span)
        return span

    def elapsed_ms(self) -> float:
        return (time.perf_counter() - self.started_at) * 1000.0


async def handle_request(ctx: RequestContext, payload: dict) -> dict:
    """Dispatches a request through the pipeline. Known concurrency hazard:
    the shared `_cache` dict is mutated from multiple tasks without a lock."""
    with ctx.span("validate"):
        validate_schema(payload)
    if payload.get("kind") == "lookup":
        key = payload["key"]
        if key in _cache:                # <-- race: read
            return _cache[key]
        value = await fetch_from_backend(key)
        _cache[key] = value              # <-- race: write
        return value
    if payload.get("kind") == "mutate":
        async with _mutation_lock:
            return await apply_mutation(ctx, payload)
    raise ValueError(f"unknown kind: {payload.get('kind')!r}")


def validate_schema(payload: dict) -> None:
    required = {"kind", "tenant"}
    missing = required - payload.keys()
    if missing:
        raise ValueError(f"missing fields: {sorted(missing)}")


async def fetch_from_backend(key: str) -> dict:
    url = f"{BACKEND_URL}/items/{key}"
    async with httpx.AsyncClient(timeout=10.0) as c:
        r = await c.get(url)
        r.raise_for_status()
        return r.json()


async def apply_mutation(ctx: RequestContext, payload: dict) -> dict:
    doc = payload["document"]
    prev = await load_document(doc["id"])
    merged = deep_merge(prev, doc)
    await write_document(merged)
    _cache.pop(doc["id"], None)
    return {"ok": True, "version": merged["version"]}


def deep_merge(a: dict, b: dict) -> dict:
    out = dict(a)
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out
'''


@dataclass
class Encoder:
    headers: dict
    encode: Callable[[dict], bytes]


ENCODINGS: dict[str, Encoder] = {
    "json": Encoder(
        headers={"Content-Type": "application/json"},
        encode=lambda p: json.dumps(p).encode(),
    ),
    "msgpack+gzip": Encoder(
        headers={
            "Content-Type": "application/vnd.msgpack",
            "Content-Encoding": "gzip",
        },
        # msgpack (inner) then gzip (outer). Server requires this order.
        encode=lambda p: gzip.compress(msgpack.packb(p)),
    ),
}


@dataclass
class RunResult:
    encoding: str
    ttft_s: float
    e2e_s: float
    bytes_sent: int


@dataclass
class Stats:
    encoding: str
    bytes_sent: int
    ttft_p50: float
    ttft_p90: float
    ttft_avg: float
    e2e_p50: float
    e2e_p90: float
    e2e_avg: float


def build_prompt() -> list[dict]:
    """Deterministic ~64k-token user message. Identical bytes every call."""
    target_chars = int(TARGET_INPUT_TOKENS * CHARS_PER_TOKEN)
    parts: list[str] = []
    i = 0
    current_chars = 0
    while current_chars < target_chars:
        parts.append(f"# block {i}\n{CODE_BLOCK}\n")
        current_chars += len(parts[-1])
        i += 1
    parts.append(
        "\nReview the function `handle_request` in block 42 for concurrency "
        "bugs and suggest a concrete fix in 3-4 sentences."
    )
    content = "".join(parts)
    approx_size = len(content.encode())
    assert approx_size < MAX_DECOMPRESSED_BYTES, (
        f"prompt too large ({approx_size} bytes) — raise MAX_DECOMPRESSED_BYTES "
        f"or lower TARGET_INPUT_TOKENS"
    )
    return [{"role": "user", "content": content}]


def parse_sse_line(line: str) -> dict | None:
    """Parse one SSE line into a payload dict, or None for empty/keepalive.

    Returns {'done': True} for the terminal '[DONE]' sentinel.
    """
    if not line or line.startswith(":"):
        return None
    if not line.startswith("data:"):
        return None
    data = line[len("data:"):].strip()
    if not data:
        return None
    if data == "[DONE]":
        return {"done": True}
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return None


def _post_and_measure(
    client: httpx.Client, body: bytes, headers: dict, encoding: str
) -> tuple[float, float]:
    """Single streaming POST. Returns (ttft_s, e2e_s). Raises on non-200."""
    ttft: float | None = None
    t0 = time.perf_counter()
    with client.stream("POST", API_URL, content=body, headers=headers) as r:
        if r.status_code != 200:
            detail = r.read().decode(errors="replace")
            # Preserve the Retry-After hint so callers can back off.
            err = RuntimeError(f"HTTP {r.status_code} for {encoding}: {detail[:500]}")
            err.status_code = r.status_code  # type: ignore[attr-defined]
            err.retry_after = r.headers.get("retry-after")  # type: ignore[attr-defined]
            raise err
        for line in r.iter_lines():
            parsed = parse_sse_line(line)
            if not parsed:
                continue
            if parsed.get("done"):
                break
            if ttft is None:
                delta = (parsed.get("choices") or [{}])[0].get("delta") or {}
                if delta.get("content"):
                    ttft = time.perf_counter() - t0
    e2e = time.perf_counter() - t0
    if ttft is None:
        # Stream closed without yielding any content token. Fall back to e2e.
        print(f"  warn: no content-bearing delta observed for {encoding}", file=sys.stderr)
        ttft = e2e
    return ttft, e2e


def run_one(client: httpx.Client, encoding: str, payload: dict, api_key: str) -> RunResult:
    """Send one streaming request, with automatic backoff on HTTP 429 (TPM limit).

    On 429 we honor the server's Retry-After header (or fall back to 30s),
    sleep, then retry the same request. Timing is reset for the retry so the
    reported TTFT/E2E reflects only the successful attempt.
    """
    enc = ENCODINGS[encoding]
    body = enc.encode(payload)
    headers = {"Authorization": f"Bearer {api_key}", **enc.headers}

    while True:
        try:
            ttft, e2e = _post_and_measure(client, body, headers, encoding)
            return RunResult(encoding=encoding, ttft_s=ttft, e2e_s=e2e, bytes_sent=len(body))
        except RuntimeError as err:
            if getattr(err, "status_code", None) != 429:
                raise
            wait = _parse_retry_after(getattr(err, "retry_after", None), default=30.0)
            print(f"  429 rate-limited; sleeping {wait:.0f}s then retrying")
            time.sleep(wait)


def _parse_retry_after(raw: str | None, default: float) -> float:
    if not raw:
        return default
    try:
        return max(1.0, float(raw))
    except ValueError:
        return default


def benchmark(
    client: httpx.Client, encoding: str, payload: dict, api_key: str, num_runs: int
) -> list[RunResult]:
    results: list[RunResult] = []
    for i in range(1, num_runs + 1):
        res = run_one(client, encoding, payload, api_key)
        results.append(res)
        size_kb = res.bytes_sent / 1024
        print(
            f"  [{encoding:>13s} {i:2d}/{num_runs}]  "
            f"ttft={res.ttft_s:5.2f}s  e2e={res.e2e_s:5.2f}s  "
            f"size={size_kb:8.1f}KB"
        )
    return results


def aggregate(results: list[RunResult]) -> Stats:
    ttfts = [r.ttft_s for r in results]
    e2es = [r.e2e_s for r in results]
    return Stats(
        encoding=results[0].encoding,
        bytes_sent=results[0].bytes_sent,
        ttft_p50=_pct(ttfts, 50),
        ttft_p90=_pct(ttfts, 90),
        ttft_avg=statistics.fmean(ttfts),
        e2e_p50=_pct(e2es, 50),
        e2e_p90=_pct(e2es, 90),
        e2e_avg=statistics.fmean(e2es),
    )


def _pct(values: list[float], p: int) -> float:
    if len(values) == 1:
        return values[0]
    quantiles = statistics.quantiles(values, n=100, method="inclusive")
    return quantiles[p - 1]


def render_chart(all_stats: list[Stats], path: str) -> None:
    encodings = [s.encoding for s in all_stats]
    ttft_p50 = [s.ttft_p50 for s in all_stats]
    e2e_p50 = [s.e2e_p50 for s in all_stats]

    x = range(len(encodings))
    width = 0.35
    fig, ax = plt.subplots(figsize=(8, 5))
    bars_ttft = ax.bar([i - width / 2 for i in x], ttft_p50, width, label="TTFT (p50)")
    bars_e2e = ax.bar([i + width / 2 for i in x], e2e_p50, width, label="E2E (p50)")

    ax.set_xticks(list(x))
    ax.set_xticklabels(encodings)
    ax.set_ylabel("Seconds")
    ax.set_title(
        f"Cerebras payload compression\n"
        f"{TARGET_INPUT_TOKENS // 1000}k input / {OUTPUT_TOKENS} output tokens, "
        f"n={NUM_RUNS}, {MODEL}"
    )
    ax.legend(loc="upper right")
    ax.grid(axis="y", alpha=0.3)

    for bars in (bars_ttft, bars_e2e):
        for bar in bars:
            h = bar.get_height()
            ax.annotate(
                f"{h:.2f}s",
                xy=(bar.get_x() + bar.get_width() / 2, h),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                fontsize=9,
            )

    for i, s in enumerate(all_stats):
        size_kb = s.bytes_sent / 1024
        label = f"{size_kb:.0f} KB" if size_kb >= 1 else f"{s.bytes_sent} B"
        ax.annotate(
            f"body: {label}",
            xy=(i, 0),
            xytext=(0, -28),
            textcoords="offset points",
            ha="center",
            fontsize=9,
            color="#555",
        )

    plt.tight_layout()
    plt.savefig(path, dpi=150)
    print(f"\nSaved chart to {path}")


def print_markdown_table(all_stats: list[Stats]) -> None:
    header = (
        "| Encoding | Bytes Sent | TTFT p50 | TTFT p90 | TTFT avg "
        "| E2E p50 | E2E p90 | E2E avg |"
    )
    sep = "|---|---|---|---|---|---|---|---|"
    print("\n" + header)
    print(sep)
    for s in all_stats:
        size_kb = s.bytes_sent / 1024
        size_str = f"{size_kb:.1f} KB" if size_kb >= 1 else f"{s.bytes_sent} B"
        print(
            f"| {s.encoding} | {size_str} "
            f"| {s.ttft_p50:.2f}s | {s.ttft_p90:.2f}s | {s.ttft_avg:.2f}s "
            f"| {s.e2e_p50:.2f}s | {s.e2e_p90:.2f}s | {s.e2e_avg:.2f}s |"
        )


def main() -> None:
    api_key = os.environ.get("CEREBRAS_API_KEY")
    if not api_key:
        raise SystemExit("CEREBRAS_API_KEY is not set. Export it before running.")

    messages = build_prompt()
    payload = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": OUTPUT_TOKENS,
        "stream": True,
    }
    plain_json_size = len(json.dumps(payload).encode())
    compressed_size = len(gzip.compress(msgpack.packb(payload)))
    print(
        f"Prompt built: plain JSON = {plain_json_size / 1024:.1f} KB, "
        f"msgpack+gzip = {compressed_size / 1024:.1f} KB "
        f"({100 * (1 - compressed_size / plain_json_size):.1f}% smaller)"
    )

    timeout = httpx.Timeout(300.0, connect=30.0)
    with httpx.Client(timeout=timeout) as client:
        print("\nWarmup (1 plain-JSON request; result discarded).")
        _ = run_one(client, "json", payload, api_key)

        all_stats: list[Stats] = []
        for encoding in ENCODINGS:
            print(f"\nBenchmarking '{encoding}' ({NUM_RUNS} runs):")
            results = benchmark(client, encoding, payload, api_key, NUM_RUNS)
            all_stats.append(aggregate(results))

    print_markdown_table(all_stats)
    render_chart(all_stats, os.path.join(os.path.dirname(__file__) or ".", "results.png"))


if __name__ == "__main__":
    main()
