import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from gist import count_words, get_client


def render_llm_metrics(navbar_placeholder):
    with navbar_placeholder.container():
        st.write("Cerebras Inference API metrics:")
        st.write(
            {
                k: v
                for k, v in st.session_state["llm_metrics"].items()
                if k != "distributions"
            }
        )
        if "gist_metrics" in st.session_state:
            st.write("GIST metrics:")
            st.write(st.session_state["gist_metrics"])


def show_inference_stat_dist(inference_stat_dist_placeholder):
    with inference_stat_dist_placeholder.container():
        inference_stat_dist_btn = st.button(
            "Show distribution of inference stats"
        )

        @st.experimental_dialog(
            "Distribution of inference stats", width="large"
        )
        def show_distribution():
            for k, v in st.session_state["llm_metrics"][
                "distributions"
            ].items():
                fig, ax = plt.subplots()
                ax.hist(np.array(v), bins=20)
                ax.set_xlabel(k)
                ax.set_ylabel("Frequency")
                st.pyplot(fig)

        if inference_stat_dist_btn:
            show_distribution()


def delete_session_state():
    for key in [
        "url",
        "pause_point",
        "pages",
        "pages_html",
        "shortened_pages",
        "llm_metrics",
        "gist_metrics",
        "inference_provider",
        "model_id",
        "client",
    ]:
        if key in st.session_state:
            del st.session_state[key]


def reset_session_state(input_url):
    st.session_state["url"] = input_url
    st.session_state["pause_point"] = 0
    st.session_state["pages"] = []
    st.session_state["pages_html"] = []
    st.session_state["shortened_pages"] = []
    st.session_state["llm_metrics"] = {
        "llm_calls": 0,
        "completion_time": 0,
        "prompt_tokens": 0,
        "response_tokens": 0,
        "total_tokens": 0,
        "avg_tokens_per_second": 0,
        "distributions": {
            "prompt_tokens": [],
            "completion_time": [],
            "tokens_per_second": [],
        },
    }
    if "gist_metrics" in st.session_state:
        del st.session_state["gist_metrics"]


def update_inference_client(inference_provider, model_id, api_key):
    if (
        (
        st.session_state.get("inference_provider") != inference_provider
        or st.session_state.get("model_id") != model_id
        ) and (api_key is not None and api_key != "")
    ):
        st.session_state["client"] = get_client(
            inference_provider, model_id, api_key=api_key
        )

    if api_key is None or api_key == "":
        st.error(f"Please set the API key before proceeding")
        if "client" in st.session_state:
            del st.session_state["client"]

def render_processed_pages(title):
    st.title(title)

    cols = st.columns(2, gap="large")
    with cols[0]:
        st.write("Original document")
        st.caption("Page boundaries are chosen by the LLM")
    with cols[1]:
        st.write("Summary")

    if len(st.session_state["pages"]) > 0:
        for i in range(len(st.session_state["pages"])):
            st.divider()
            st.caption(f'GIST Page {i}')
            cols = st.columns(2, gap="large")
            with cols[0]:
                for p in st.session_state["pages_html"][i]:
                    st.markdown(p, unsafe_allow_html=True)
            with cols[1]:
                st.write(st.session_state["shortened_pages"][i])
        html_elem = f"<div id=\"page-{st.session_state['pause_point']}\" style=\"height: 0px;\"></div>"
        html_elem += "<script>console.log(\"hello world!\"); setTimeout(function(){document.getElementById(\"page-"
        html_elem += str(st.session_state["pause_point"])
        html_elem += (
            "\").scrollIntoView({\"behavior\": \"smooth\"});}, 10);</script>"
        )
        st.components.v1.html(html_elem, height=0)


def render_new_page():
    st.divider()
    st.caption(f'GIST Page {len(st.session_state["pages"])}')
    cols = st.columns(2, gap="large")
    with cols[0]:
        for p in st.session_state["pages_html"][-1]:
            st.markdown(p, unsafe_allow_html=True)

    html_elem = f"<div id=\"page-{st.session_state['pause_point']}\" style=\"height: 5px;\"></div>"
    html_elem += "<script>setTimeout(function(){document.getElementById(\"page-"
    html_elem += str(st.session_state["pause_point"])
    html_elem += (
        "\").scrollIntoView({\"behavior\": \"smooth\"});}, 10);</script>"
    )
    st.components.v1.html(html_elem, height=2)
    return cols


def unpack_summary(streaming_text):
    summary_page = ""
    for chunk in streaming_text:
        summary_page += chunk
        yield chunk
    st.session_state["shortened_pages"].append(summary_page)


def compute_gist_metrics():
    st.session_state["gist_metrics"] = {}
    st.session_state["gist_metrics"]["document_words"] = sum(
        count_words(paragraph)
        for page in st.session_state["pages"]
        for paragraph in page
    )

    st.session_state["gist_metrics"]["summary_words"] = sum(
        count_words(summary) for summary in st.session_state["shortened_pages"]
    )

    st.session_state["gist_metrics"]["compression_rate"] = 100 * (
        1
        - st.session_state["gist_metrics"]["summary_words"]
        / st.session_state["gist_metrics"]["document_words"]
    )
