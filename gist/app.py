import streamlit as st
from arxiv_parser import (
    get_ar5iv_link,
    get_bibliography_from_html,
    get_html_page,
    get_paragraphs_from_html,
    get_title_from_html,
)
from gist import answer_question, create_summary, get_next_page_break
from streamlit_helper import (
    compute_gist_metrics,
    delete_session_state,
    render_llm_metrics,
    render_new_page,
    render_processed_pages,
    reset_session_state,
    show_inference_stat_dist,
    unpack_summary,
    update_inference_client,
)

if __name__ == "__main__":
    st.set_page_config(page_title="Arxiv GIST", layout="wide")

    with st.sidebar.container():
        inference_provider = st.selectbox(
            "Inference Provider",
            ("Cerebras", "Fireworks"),
            on_change=delete_session_state,
        )
        if inference_provider == "Cerebras":
            model_name_to_id = {"Llama 3.1 8B Instruct": "llama3.1-8b"}
        elif inference_provider == "Fireworks":
            model_name_to_id = {
                "Llama 3.1 8B Instruct": "accounts/fireworks/models/llama-v3p1-8b-instruct"
            }

        model = st.selectbox(
            "Model", model_name_to_id.keys(), on_change=delete_session_state
        )
        model_id = model_name_to_id[model]
        api_key = st.text_input(
            f"{inference_provider} API Key", type="password"
        )
        update_inference_client(
            inference_provider, model_id, api_key
        )

        navbar_placeholder = st.sidebar.empty()
        inference_stat_dist_placeholder = st.sidebar.empty()

    st.title("Q&A Arxiv papers via GIST")
    st.write(
        """Current Large Language Models (LLMs) are not only limited to some maximum context length, but also
are not able to robustly consume long inputs. GIST addresses this by proposing a human-inspired reading agent.
1. The model "reads" a document and breaks it into "pages".
2. Each page is then summarized.
3. During Q&A, the model is given the summaries of each page and asked if it wants to expand ("reread") any of the pages.
4. The summaries of all pages + whichever pages the model chose to expand are used to answer the question.

This approach allows the model to retain the high level flow of the original document while mixing granularities that allow it to capture the finer details that are needed to answer a specific question.
Read more about GIST here: https://arxiv.org/pdf/2402.09727
"""
    )

    input_url = st.text_input(
        "Arxiv link:", placeholder="https://arxiv.org/pdf/1706.03762"
    )

    if input_url:
        if st.session_state.get("client") is None:
            st.stop()

        ar5iv_url = get_ar5iv_link(input_url)
        page_html = get_html_page(ar5iv_url)
        title = get_title_from_html(page_html)
        bib = get_bibliography_from_html(page_html)
        if title is None:
            st.error(
                f"This app uses arxiv's experimental ar5iv html API. Unfortunately, "
                f"it seems as though ar5iv doesn't support this paper. Your link:"
                f"{input_url}. Ar5iv link (which seems to be broken): {ar5iv_url}"
            )
            st.stop()

        paragraphs, paragraphs_html = get_paragraphs_from_html(page_html)

        if (
            "pause_point" not in st.session_state
            or "url" not in st.session_state
            or st.session_state["url"] != input_url
        ):
            reset_session_state(input_url)

        render_llm_metrics(navbar_placeholder)
        render_processed_pages(title)

        # Phase 1: Preprocessing the arxiv paper.
        # The LLM will iteratively group paragraphs together based on
        # narration by selecting "pause points". Paragraphs contained from the
        # old pause point to the new pause point are referred to as a "page". The
        # LLM then summarizes this new page into a summarized page.
        while st.session_state["pause_point"] < len(paragraphs):
            old_pause_point = st.session_state["pause_point"]
            st.session_state["pages"], new_pause_point = get_next_page_break(
                st.session_state["client"],
                title,
                paragraphs,
                st.session_state["pages"],
                old_pause_point,
                llm_metrics=st.session_state["llm_metrics"],
                verbose=False,
            )

            page_html = paragraphs_html[old_pause_point:new_pause_point]
            st.session_state["pages_html"].append(page_html)
            st.session_state["pause_point"] = new_pause_point
            added_page_idx = len(st.session_state["pages"]) - 1

            render_llm_metrics(navbar_placeholder)
            cols = render_new_page()

            with cols[1]:
                summary_stream = create_summary(
                    st.session_state["client"],
                    title,
                    st.session_state["pages"][added_page_idx],
                    llm_metrics=st.session_state["llm_metrics"],
                    verbose=False,
                    stream=True,
                )
                st.write_stream(unpack_summary(summary_stream))
                render_llm_metrics(navbar_placeholder)

        with st.expander("Bibliography"):
            st.markdown(bib, unsafe_allow_html=True)

        compute_gist_metrics()
        render_llm_metrics(navbar_placeholder)
        show_inference_stat_dist(inference_stat_dist_placeholder)

        question = st.text_input("Question:")
        if question:
            intermediate, answer_stream = answer_question(
                st.session_state["client"],
                title,
                st.session_state["pages"],
                st.session_state["shortened_pages"],
                question,
                llm_metrics=st.session_state["llm_metrics"],
                verbose=False,
                stream=True,
            )
            if not isinstance(intermediate, str):
                st.error(intermediate)
                st.stop()

            with st.expander("Show reader's thoughts"):
                st.write(intermediate)
            st.write_stream(answer_stream)
            render_llm_metrics(navbar_placeholder)
