# Marketing Agent

## Overview

This project is an automated marketing agent that uses Large Language Models (LLMs) to create tailored marketing content across various channels. It leverages different AI models for reasoning and search tasks to generate comprehensive marketing strategies and copy.

The Marketing Agent is designed as an LLM agent that emulates a typical workflow for generating marketing copy. It demonstrates how to build hybrid software that mixes traditional software with LLMs to automate complex decision-making processes both robustly and flexibly.

## Features

- Generate marketing campaigns based on product descriptions
- Support for multiple marketing channels (email, Twitter, LinkedIn, blog posts, press releases, video scripts, and GitHub project descriptions)
- Customizable number of content revisions to iteratively improve copy using an LLM
- Choice of AI providers (Cerebras, Fireworks, Groq, Together) for reasoning tasks
- Optional use of Perplexity for search and information retrieval tasks
- Hallucination mode to disable Perplexity search and use a static LLM instead
- Structured output generation for robust LLM calls
- Plugin model for extensible support of various marketing channels

## Setup

1. please consult the setup in the respective README files for both [server](https://github.com/Cerebras/inference-examples/tree/main/marketing-agent/server) and [client](https://github.com/Cerebras/inference-examples/tree/main/marketing-agent/client)
2. run `bash run.sh` to start the server and client from the project root
