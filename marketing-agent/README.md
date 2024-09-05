# Marketing Agent

| ![Overview of the marketing agent workflow](https://github.com/ThatOneDevGuy/marketing-agent/blob/public-demo/images/design.png?raw=true) |
|:--:|
| *Overview of the marketing agent workflow.* |

## Overview

This project is an automated marketing agent that uses Large Language Models (LLMs) to create tailored marketing content across various channels. It leverages different AI models for reasoning and search tasks to generate comprehensive marketing strategies and copy.

The Marketing Agent is designed as an LLM agent that emulates a typical workflow for generating marketing copy. It demonstrates how to build hybrid software that mixes traditional software with LLMs to automate complex decision-making processes both robustly and flexibly.

Visit our [demo](https://marketing-assistant.ai4m.com/) to try marketing agent for yourself. 

## Features

- Generate marketing campaigns based on product descriptions
- Support for multiple marketing channels (email, Twitter, LinkedIn, blog posts, press releases, video scripts, and GitHub project descriptions)
- Customizable number of content revisions to iteratively improve copy using an LLM
- Choice of AI providers (Cerebras, Fireworks, Groq, Together) for reasoning tasks
- Optional use of Perplexity for search and information retrieval tasks
- Hallucination mode to disable Perplexity search and use a static LLM instead
- Structured output generation for robust LLM calls
- Plugin model for extensible support of various marketing channels

## Key Components

1. **Workflow** (`campaign.py`): Implements a five-phase process for campaign generation:
   - Brainstorming key value propositions
   - Identifying markets and audience demographics
   - Determining appropriate marketing channels
   - Creating content strategies
   - Generating and iterating on marketing copy

2. **LLM Engines**: Interfaces for different LLM providers (Cerebras, Fireworks, Groq, Together, Perplexity)

3. **Copy Plugins**: Extensible system for defining different types of marketing copy (e.g., blog posts, tweets, LinkedIn posts)

4. **Structured Output Generation**: Utilizes Pydantic for creating robust, schema-based outputs from LLMs

## Installation

1. Clone this repository:
   ```
   git clone git@github.com:ThatOneDevGuy/marketing-agent.git
   ```
2. Obtain API keys for Cerebras and Perplexity (if using search functionality) and add them to your environment.
3. Copy the `.env.example` file to `.env` and add your API keys.
4. Install the required dependencies with `poetry install`.

## Usage

Run the script from the command line:

```
poetry run python src/main.py [product_description_file] [options]
```

### Arguments:

- `product_description_file`: Path to the file containing the product description. Use `-` to read from standard input.

### Options:

- `-o, --output`: Output directory path (default: current working directory)
- `-r, --revisions`: Number of content revisions (default: 1)
- `-p, --provider`: AI provider for reasoning (choices: cerebras, fireworks, groq, together; default: cerebras)
- `-m, --reasoning-model`: Provider-specific model name for reasoning (default: llama3.1-70b)
- `-s, --search-model`: Perplexity model name for search (default: llama-3.1-sonar-large-128k-online)
- `--hallucinate`: Enable hallucination mode (disables Perplexity search)

### Example:

```
echo "A very fast LLM inference API" | poetry run python src/main.py -
```

## Project Structure

- `__main__.py`: Entry point of the application
- `campaign.py`: Core logic for campaign generation
- `marketing_copy.py`: Handles creation and improvement of marketing copy
- `llm/`: Directory containing LLM interfaces
   - `base_engine.py`: Utility functions for structured output generation
   - `*_engine.py`: Interfaces for different LLM providers
- `datatypes.py`: Defines data structures used across the project
- `copy_plugins/`: Directory containing plugins for different marketing channels
  - `email.py`, `twitter_thread.py`, `linkedin_post.py`, etc.: Channel-specific copy generators
  - `globals.py`: Global configurations for copy plugins
  - `__init__.py`: Initializes the copy plugins package

## Design Philosophy

This project demonstrates how to create hybrid software that combines traditional programming with LLM capabilities:

1. The workflow is implemented primarily using traditional software to encode expert knowledge, making it more robust than deferring all control flow to the LLM.
2. Structured outputs are used to interface between traditional software and LLMs, allowing for precise control over LLM responses.
3. The system uses natural language to specify tasks, inputs, and outputs, enabling the workflow to handle a wide variety of products.
4. The copy plugin system allows for easy extension to new marketing channels and content types.

## Performance Considerations

The project is designed to take advantage of fast inference capabilities, such as those provided by the Cerebras API. This is particularly beneficial for the iterative copy improvement process, which can require multiple sequential LLM generations.

