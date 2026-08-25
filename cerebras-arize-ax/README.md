# Cerebras and Arize AX

This project shows how to trace Cerebras Inference calls in [Arize AX](https://arize.com/docs/ax/integrations/llm-providers/cerebras/cerebras-tracing) with the OpenAI-compatible API and the OpenInference OpenAI instrumentor.

Use Arize AX when you want a managed workspace for production LLM tracing, monitoring,
and evaluation workflows. Use [Arize Phoenix](https://inference-docs.cerebras.ai/integrations/arize-phoenix)
when you want an open-source or self-hosted observability path for Cerebras applications.

## Features

- Trace Cerebras chat completions through the OpenAI-compatible endpoint
- Capture prompt, response, model, token, latency, and error metadata in Arize AX
- Use OpenInference instrumentation without a Cerebras-specific tracing SDK
- Connect production traces to LLM and agent evaluation workflows

## Installation

Install the OpenAI client, Arize OpenTelemetry exporter, and OpenInference OpenAI instrumentation:

```bash
pip install openai arize-otel openinference-instrumentation-openai
```

Set your Cerebras and Arize credentials:

```bash
export CEREBRAS_API_KEY=your_cerebras_api_key_here
export CEREBRAS_MODEL=gpt-oss-120b
export ARIZE_SPACE_ID=your_arize_space_id_here
export ARIZE_API_KEY=your_arize_api_key_here
export ARIZE_PROJECT_NAME=cerebras-arize-ax
```

## Example

Instrument the OpenAI SDK before creating the Cerebras client:

```python
import os

from arize.otel import register
from openinference.instrumentation.openai import OpenAIInstrumentor

tracer_provider = register(
    space_id=os.environ["ARIZE_SPACE_ID"],
    api_key=os.environ["ARIZE_API_KEY"],
    project_name=os.environ["ARIZE_PROJECT_NAME"],
)
OpenAIInstrumentor().instrument(tracer_provider=tracer_provider)

from openai import OpenAI

client = OpenAI(
    api_key=os.environ["CEREBRAS_API_KEY"],
    base_url="https://api.cerebras.ai/v1",
)

response = client.chat.completions.create(
    model=os.environ["CEREBRAS_MODEL"],
    messages=[
        {
            "role": "user",
            "content": "Why does fast inference still need observability?",
        }
    ],
    max_completion_tokens=500,
)

print(response.choices[0].message.content)
```

After the request completes, open the `cerebras-arize-ax` project in Arize AX to inspect the trace.

## Evaluation

Traces give teams the raw material for quality work after deployment: reviewing failure
cases, comparing prompt versions, measuring latency and cost, and grading model or agent
behavior. For more detail, see Arize's guides to
[LLM evaluation](https://arize.com/resources/llm-evaluation/) and
[agent evaluation](https://arize.com/guides/ai-agent-handbook/agent-evaluation/).

## Further reading

- [Cerebras Inference documentation](https://inference-docs.cerebras.ai/)
- [OpenInference OpenAI instrumentor](https://github.com/Arize-ai/openinference/tree/main/python/instrumentation/openinference-instrumentation-openai)
- [Arize AX Cerebras tracing guide](https://arize.com/docs/ax/integrations/llm-providers/cerebras/cerebras-tracing)
