# ReadAgent for Arxiv Papers

## Overview

This project implements Google DeepMind’s ReadAgent using the Cerebras SDK. It leverages the ReadAgent workflow to enable users to interactively chat with Arxiv papers. Try our demo here! 

ReadAgent is an AI agent designed to enhance the capabilities of Large Language Models (LLMs) in processing and understanding long contexts through a method called memory gisting. Inspired by human reading patterns, ReadAgent employs a novel approach centered around the concept of “gist memories” to break down, summarize, and intelligently retrieve information from lengthy texts, such as books or extensive documents.

For a detailed description of ReadAgent’s workflow, please refer to our project blog post and the [original paper](https://arxiv.org/abs/2402.09727) by Google DeepMind.

ReadAgent's workflow involves multiple prompts to the LLM at each step to create pages, generate summaries, and retrieve relevant information. As a result, the efficiency of ReadAgent heavily depends on a low-latency LLM inference solution, like the one provided by Cerebras.

## Project Structure

`app.py`: Entry point of the application
`gist.py`: Core logic of ReadAgent
`arxiv_parser.py`: Handles processing of papers from Arxiv
`streamlit_helper.py`: Handles UI rendering with Streamlit

## Setup & Usage

- Clone the repository
- Install the requirements `pip install -r requirements.txt`
- See the Cerebras SDK [QuickStart guide](https://inference-docs.cerebras.ai/quickstart) for configuring your API key
- Run the app `streamlit run app.py`

## References

- Lee, Kuang-Huei, Chen, Xinyun, Furuta, Hiroki, Canny, John, and Fischer, Ian. "A Human-Inspired Reading Agent with Gist Memory of Very Long Contexts." *arXiv preprint arXiv:2402.09727*, 2024. [Link to paper](https://arxiv.org/abs/2402.09727)
