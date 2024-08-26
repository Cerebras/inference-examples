import os
import re
from typing import List, Optional, Tuple

import requests
from bs4 import BeautifulSoup


def get_ar5iv_link(url: str) -> str:
    # Turns an arxiv link into a ar5iv link
    if url.startswith("https://ar5iv.labs.arxiv.org/html/"):
        ar5iv_url = url
    else:
        match = re.match(r"https\:\/\/arxiv\.org\/\w+\/([\w+.]*)", url)

        assert match is not None, f"{url} is not a valid arxiv link!"
        paper_id = match.group(1)
        ar5iv_url = f"https://ar5iv.labs.arxiv.org/html/{paper_id}"

    return ar5iv_url


def get_html_page(url: str) -> str:
    # Fetches html contained at the supplied url.
    # Pages are cached so that we don't keep hitting arxiv's servers if we
    # make multiple requests for the same paper
    if not os.path.exists("html_cache"):
        os.makedirs("html_cache")

    cache_key = url[url.rfind("/") + 1 :]
    file_path = os.path.join("html_cache", cache_key)
    if os.path.exists(file_path):
        # Cache hit
        with open(file_path, "r") as f:
            return f.read()
    else:
        # Cache miss
        response = requests.get(url)
        assert response.status_code == 200

        with open(file_path, "w") as f:
            f.write(response.text)
            return response.text


def get_title_from_html(html: str) -> str:
    # Extracts the title from an ar5iv webpage
    soup = BeautifulSoup(html, 'html.parser')
    element = soup.find(class_="ltx_title_document")
    if element is None:
        return None
    title = element.get_text()
    title = " ".join([fragment.strip() for fragment in title.split("\n")])
    return title


def get_paragraphs_from_html(html: str) -> Tuple[List[str], List[str]]:
    # Extracts a list of paragraphs from the arxiv webpage. The function returns
    # a human/llm readable representation, and also an html representation which
    # can be directly rendered. The html representation is useful in scenarios
    # where the paragraphs contained custom styling such as latex.

    soup = BeautifulSoup(html, 'html.parser')
    # Try to get all paragraphs *after* title
    element = soup.find(class_="ltx_title_document")
    if element is None:
        elements = soup.find_all(class_="ltx_p")
    else:
        elements = element.find_all_next(class_="ltx_p")

    original_html = [str(e) for e in elements]
    llm_readable = []

    for e in elements:
        math_tags = e.find_all('math')
        for math_tag in math_tags:
            alttext = math_tag.get("alttext", None)
            if alttext is not None:
                alttext = "$" + alttext + "$"
                math_tag.replace_with(alttext)
        llm_readable.append(e.get_text())

    return llm_readable, original_html


def get_bibliography_from_html(html) -> Optional[str]:
    # Extracts the bibliography from an arxiv webpage. A bibliography does not
    # exist, returns None.
    soup = BeautifulSoup(html, 'html.parser')
    # Try to get all paragraphs *after* title
    bib = soup.find(id="bib")
    if bib is None:
        return None
    biblist = bib.find_next(class_="ltx_biblist")
    if biblist is None:
        return str(bib)
    return str(biblist)
