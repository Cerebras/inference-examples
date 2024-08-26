import re
import time
from dataclasses import dataclass
from typing import Union

from fireworks.client import Fireworks
from openai import OpenAI

from cerebras.cloud.sdk import Cerebras


@dataclass
class ClientContainer:
    client: Union[OpenAI, Cerebras, Fireworks]
    model: str


def get_client(inference_provider, model, base_url=None, api_key=None):
    if inference_provider == "OpenAI":
        client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )
    elif inference_provider == "Cerebras":
        client = Cerebras(base_url=base_url, api_key=api_key)
    elif inference_provider == "Fireworks":
        client = Fireworks(base_url=base_url, api_key=api_key)
    else:
        raise RuntimeError(
            f"Unrecognized inference provider: {inference_provider}"
        )
    return ClientContainer(client, model)


def update_llm_metrics(llm_metrics, response, delta_time):
    if hasattr(response, "time_info"):
        time_taken = response.time_info.completion_time
    else:
        time_taken = delta_time
    llm_metrics["llm_calls"] += 1
    llm_metrics["completion_time"] += time_taken
    llm_metrics["prompt_tokens"] += response.usage.prompt_tokens
    llm_metrics["response_tokens"] += response.usage.completion_tokens
    llm_metrics["total_tokens"] += response.usage.total_tokens
    llm_metrics["avg_tokens_per_second"] = (
        llm_metrics["response_tokens"] / llm_metrics["completion_time"]
    )
    llm_metrics["curr_tokens_per_second"] = (
        response.usage.completion_tokens / time_taken
    )
    llm_metrics["distributions"]["prompt_tokens"].append(
        response.usage.prompt_tokens
    )
    llm_metrics["distributions"]["completion_time"].append(time_taken)
    llm_metrics["distributions"]["tokens_per_second"].append(
        response.usage.completion_tokens / time_taken
    )


def unpack_streaming_response(
    response, startime, llm_metrics=None, verbose=False
):
    for chunk in response:
        if verbose:
            print(chunk)
        iterator = chunk.choices
        for message in iterator:
            if message.delta.content is not None:
                yield message.delta.content

            finish_reason = message.finish_reason
            if finish_reason is not None and llm_metrics is not None:
                endtime = time.time()
                update_llm_metrics(llm_metrics, chunk, endtime - startime)


def run_llm(
    client_container: ClientContainer,
    messages,
    llm_metrics=None,
    verbose=False,
    stream=False,
):
    startime = time.time()
    response = client_container.client.chat.completions.create(
        model=client_container.model,
        messages=messages,
        stream=stream,
    )
    if not stream:
        if llm_metrics is not None:
            endtime = time.time()
            update_llm_metrics(llm_metrics, response, endtime - startime)
        return response.choices[0].message.content
    else:
        return unpack_streaming_response(
            response, startime, llm_metrics=llm_metrics, verbose=verbose
        )


prompt_pagination_template = """
You are given a passage that is taken from a larger text (article, book, ...) and some numbered labels between the paragraphs in the passage.
Numbered label are in angeled brackets. For example, if the label number is 19, it shows as <19> in text.
Please choose one label that it is natural to break reading.
Such point can be scene transition, end of a dialogue, end of an argument, narrative transition, etc.
Please answer the break point label and explain.
For example, if <57> is a good point to break, answer with \"Break point: <57>\n Because ...\"

Passage:

{0}
{1}
{2}

"""


def parse_pause_point(text):
    text = text.strip("Break point: ")
    if text[0] != '<':
        return None
    for i, c in enumerate(text):
        if c == '>':
            if text[1:i].isnumeric():
                return int(text[1:i])
            else:
                return None
    return None


def count_words(text):
    """Simple word counting."""
    return len(text.split())


def get_next_page_break(
    client_container,
    title,
    paragraphs,
    pages,
    start_paragraph,
    word_limit=600,
    start_threshold=280,
    verbose=True,
    llm_metrics=None,
    allow_fallback_to_last=True,
):

    print(f"[Pagination][Article {title}]")

    i = start_paragraph

    preceding = "" if i == 0 else "...\n" + '\n'.join(pages[-1])
    passage = [paragraphs[i]]
    wcount = count_words(paragraphs[i])
    j = i + 1
    while wcount < word_limit and j < len(paragraphs):
        wcount += count_words(paragraphs[j])
        if wcount >= start_threshold:
            passage.append(f"<{j}>")
        passage.append(paragraphs[j])
        j += 1
    passage.append(f"<{j}>")
    end_tag = "" if j == len(paragraphs) else paragraphs[j] + "\n..."

    pause_point = None
    if wcount < 350:
        pause_point = len(paragraphs)
    else:
        prompt = prompt_pagination_template.format(
            preceding, '\n'.join(passage), end_tag
        )
        response = run_llm(
            client_container,
            [{"role": "user", "content": prompt}],
            llm_metrics=llm_metrics,
            verbose=verbose,
        )
        pause_point = parse_pause_point(response)
        if pause_point and (pause_point <= i or pause_point > j):
            print(f"prompt:\n{prompt},\nresponse:\n{response}\n")
            print(f"i:{i} j:{j} pause_point:{pause_point}")
            pause_point = None
        if pause_point is None:
            if allow_fallback_to_last:
                pause_point = j
            else:
                raise ValueError(f"prompt:\n{prompt},\nresponse:\n{response}\n")

    page = paragraphs[i:pause_point]
    pages.append(page)
    if verbose:
        print(f"Paragraph {i}-{pause_point-1}", page)

    return pages, pause_point


prompt_shorten_template = """
Please shorten the following passage.
Just give me a shortened version. DO NOT explain your reason.

Passage:
{}

"""


def post_process_response(text: str) -> str:
    match = re.match(r"(here[a-z ]+ shortened.*?\:)", text.lower())
    if match is not None:
        text = text[len(match.group(1)) :].strip()
    return text


def create_summary(
    client_container, title, page, llm_metrics=None, verbose=True, stream=False
):
    prompt = prompt_shorten_template.format('\n'.join(page))
    response = run_llm(
        client_container,
        [
            {"role": "user", "content": prompt},
        ],
        llm_metrics=llm_metrics,
        verbose=verbose,
        stream=stream,
    )

    # Llama models (specifically the 8B) have trouble producing the summary
    # without prefixing its response with something like
    # "here is a shortened ...". We need to apply post-processing to strip
    # this out.
    if not stream:
        shortened_text = response.strip()
        shortened_text = post_process_response(shortened_text)
        return shortened_text
    else:
        # Post processing is a little tricky in the streaming case. One solution
        # is to accumulate all chunks until the first newline. We can then
        # post-process the first line (since this is the only section we might
        # want to change). After that, we can yield all subsequent chunks as
        # we regularly would.
        def strip_streaming(streaming_text):
            first_chunk = ""
            for chunk in streaming_text:
                first_chunk += chunk
                if first_chunk.find("\n") != -1:
                    break
            first_chunk = post_process_response(first_chunk)
            yield first_chunk
            for chunk in streaming_text:
                yield chunk

        return strip_streaming(response)


prompt_lookup_template = """
The following text is what you remembered from reading an article and a multiple choice question related to it.
You may read 1 to 6 page(s) of the article again to refresh your memory to prepare yourself for the question.
Please respond with which page(s) you would like to read.
For example, if your only need to read Page 8, respond with \"I want to look up Page [8] to ...\";
if your would like to read Page 7 and 12, respond with \"I want to look up Page [7, 12] to ...\";
if your would like to read Page 2, 3, 7, 15 and 18, respond with \"I want to look up Page [2, 3, 7, 15, 18] to ...\".
if your would like to read Page 3, 4, 5, 12, 13 and 16, respond with \"I want to look up Page [3, 3, 4, 12, 13, 16] to ...\".
DO NOT select more pages if you don't need to.
DO NOT answer the question yet.

Text:
{}

Question:
{}

Take a deep breath and tell me: Which page(s) would you like to read again?
"""

prompt_mc_answer_template = """
Read the following article and answer a multiple choice question.
For example, if (C) is correct, answer with \"Answer: (C) ...\"

Article:
{}

Question:
{}
{}

"""

prompt_free_answer_template = """
Read the following article and then answer the question.

Article:
{}

Question:
{}

"""


def answer_question(
    client_container,
    title,
    pages,
    shortened_pages,
    question,
    llm_metrics=None,
    verbose=True,
    stream=False,
):
    shortened_pages_pidx = []
    for i, shortened_text in enumerate(shortened_pages):
        shortened_pages_pidx.append(f"\nPage {i}:\n" + shortened_text)
    shortened_article = '\n'.join(shortened_pages_pidx)

    prompt_lookup = prompt_lookup_template.format(shortened_article, question)

    page_ids = []

    intermediate_response = run_llm(
        client_container,
        [{"role": "user", "content": prompt_lookup}],
        llm_metrics=llm_metrics,
        verbose=verbose,
        stream=False,
    )
    if not isinstance(intermediate_response, str):
        return intermediate_response, None
    intermediate_response = intermediate_response.strip()

    try:
        start = intermediate_response.index('[')
    except ValueError:
        start = len(intermediate_response)
    try:
        end = intermediate_response.index(']')
    except ValueError:
        end = 0
    if start < end:
        page_ids_str = intermediate_response[start + 1 : end].split(',')
        page_ids = []
        for p in page_ids_str:
            if p.strip().isnumeric():
                page_id = int(p)
                if page_id < 0 or page_id >= len(pages):
                    print("Skip invalid page number: ", page_id, flush=True)
                else:
                    page_ids.append(page_id)

    if verbose:
        print("Model chose to look up page {}".format(page_ids))

    # Memory expansion after look-up, replacing the target shortened page with the original page
    expanded_shortened_pages = shortened_pages[:]
    if len(page_ids) > 0:
        for page_id in page_ids:
            expanded_shortened_pages[page_id] = '\n'.join(pages[page_id])

    expanded_shortened_article = '\n'.join(expanded_shortened_pages)
    if verbose:
        print(
            "Expanded shortened article:\n",
            expanded_shortened_article,
            flush=True,
        )
    prompt_answer = prompt_free_answer_template.format(
        expanded_shortened_article, question
    )

    answer = run_llm(
        client_container,
        [{"role": "user", "content": prompt_answer}],
        llm_metrics=llm_metrics,
        verbose=verbose,
        stream=stream,
    )
    if not stream:
        answer = answer.strip()

    return intermediate_response, answer
