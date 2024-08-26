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

1. Clone this repository.
2. Copy the `.env.example` file to `.env` and fill in the appropriate values.
3. Install the required dependencies `poetry install`

## Usage

1. run `poetry shell` to create or enter a virtual environment
2. run `python src/main.py` to start the server

## Project Structure

- `__main__.py`: Entry point of the application
- `campaign.py`: Core logic for campaign generation
- `marketing_copy.py`: Handles creation and improvement of marketing copy
- `datatypes.py`: Defines data structures used across the project
- `llm/`: Interfaces for different LLM providers
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

## Contact

[Cerebras] - [email for point of contact]

Project Link: [link to repo where this will be hosted](http://link)
