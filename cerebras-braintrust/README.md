# Cerebras and Braintrust

[![](imgs/cerebras_braintrust.png)]()

This project demonstrates how to use [Braintrust](https://www.braintrust.dev/) with the [Cerebras Cloud SDK](https://inference-docs.cerebras.ai/introduction) for evaluating,
logging, and protyping LLM applications.

## Features

- Trace Cerebras model calls with Braintrust
- Run evals on Cerebras models to compare them to other models and providers
- Log production data calls to Cerebras models
- Create LLM-as-a-Judge scorers backed by Cerebras models

## Installation

Braintrust works best with the OpenAI client, which automatically supports Cerebras models.

1. Install Braintrust and OpenAI clients:

```bash
pip install braintrust openai
```

2. Set up your Braintrust API key and Cerebras API key as environment variables:

```bash
export BRAINTRUST_API_KEY=your_api_key_here
export CEREBRAS_API_KEY=your_api_key_here
```

3. Initialize the OpenAI client with your Cerebras API key and the Braintrust wrapper:

```python
import os

import openai
import braintrust

client = braintrust.wrap_openai(openai.OpenAI(
    api_key=os.getenv("CEREBRAS_API_KEY"),
    base_url="https://api.cerebras.ai/v1",
))
```

## Examples

- [Cerebras-Braintrust-Eval.ipynb](./cerebras_braintrust_eval.ipynb) walks evals, logging, and tracing with Cerebras models and Braintrust.
- [Cerebras-Braintrust-Scoring.md](./cerebras_braintrust_scoring.md) shows how to create an LLM-as-a-Judge scorer using a Cerebras model and Braintrust.

## Further reading

For more information on using Braintrust for model evaluations, visit the [Braintrust documentation](https://www.braintrust.dev/docs/guides/evals).
