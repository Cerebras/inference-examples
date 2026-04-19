"""Minimal example: send a chat completion request with msgpack+gzip compression.

Cerebras Inference accepts compressed request bodies on /v1/chat/completions.
The strongest combination is msgpack (inner) + gzip (outer). Order is not swappable.
"""

import gzip
import json
import os

import httpx
import msgpack

API_URL = "https://api.cerebras.ai/v1/chat/completions"
MODEL = "gpt-oss-120b"

api_key = os.environ.get("CEREBRAS_API_KEY")
if not api_key:
    raise SystemExit("CEREBRAS_API_KEY is not set. Export it before running.")

payload = {
    "model": MODEL,
    "messages": [{"role": "user", "content": "Explain payload compression in one sentence."}],
    "max_tokens": 1024,
}

plain_json = json.dumps(payload).encode()
body = gzip.compress(msgpack.packb(payload))

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/vnd.msgpack",
    "Content-Encoding": "gzip",
}

with httpx.Client(timeout=60.0) as client:
    r = client.post(API_URL, content=body, headers=headers)
    r.raise_for_status()
    reply = r.json()["choices"][0]["message"]["content"]

print(reply)
print()
print(f"Sent {len(body)} compressed bytes (vs {len(plain_json)} plain JSON — "
      f"{100 * (1 - len(body) / len(plain_json)):.1f}% smaller).")
