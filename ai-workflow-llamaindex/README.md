## "Alien" Agentic Workflows: LlamaIndex

This tutorial outlines the setup, code structure, and the implementation of a simple agentic workflow using Cerebras and LlamaIndex.

![finished product](./alienMath.png)

### Step 1: Set up your API Key

1. **Obtain Your API Key**: Log in to your Cerebras account, navigate to the “API Keys” section, and generate a new API key.

2. **Set the API Key in the Sidebar**: Once you have the Cerebras API key, add it to the sidebar on the left.

### Step 2: Install the Cerebras Inference Library

You need to install the Cerebras Inference library to interact with the API. Use the following command to install the library along with other dependencies:

```bash
pip install https://cerebras-cloud-sdk.s3.us-west-1.amazonaws.com/test/cerebras_cloud_sdk-0.5.0-py3-none-any.whl
pip install -r requirements.txt
```

### Step 3: Start decoding alien messages

Run the command `streamlit run main.py` to start up the frontend.

### What is an agentic workflow?
Within the context of LlamaIndex, an agent is a software component driven by a large language model (LLM). It's assigned a task performs a sequence of actions to achieve it.

The agent is equipped with a range of tools, which can include anything from basic functions to comprehensive LlamaIndex query engines. **In this example, we'll be creating `poof` and `shoop` tools to decode an alien math language.**

The agent evaluates these tools to determine the most effective one for each step. Once a step is completed, the agent assesses whether the task is finished and, if so, delivers the result to the user. If the task is not yet complete, the agent returns to the beginning of the process to continue with the next step. **You can see this workflow in action from the output of your request.**

### Code Overview

#### 1. Define Basic Tools

The `poof` and `shoop` functions define custom alien math operations:

```python
def poof(a: float, b: float) -> float:
    """Poofs two numbers and returns the product of the two numbers and 3"""
    return a * b * 3

def shoop(a: float, b: float) -> float:
    """Shoops two numbers and returns the sum of the two numbers and 3"""
    return a + b + 3
```

- `poof` computes the product of two numbers and multiplies the result by 3.
- `shoop` computes the sum of two numbers and adds 3.

`FunctionTool` is used to wrap the custom functions for use with the LlamaIndex agent:

```python
from llama_index.core.tools import FunctionTool

poof_tool = FunctionTool.from_defaults(fn=poof)
shoop_tool = FunctionTool.from_defaults(fn=shoop)
```

- `FunctionTool.from_defaults` wraps the custom functions to be used as tools by the agent.

### 2. Processing User Input and Creating the Agent

The application collects user input for "alien" math problems:

```python
user = st.text_input("")
st.info("ex: What is 2 shoop 3 poof 1 shoop 4?")
```

We then initialize the agent and LLM in order to be able to start the workflow.

```python
if st.button("Generate output"):
    if user:
        llm = Groq(model="llama3-70b-8192", api_key=api_key)
        agent = ReActAgent.from_tools([poof_tool, shoop_tool], llm=llm, verbose=True, max_iterations=100)
```
- `Cerebras` will allow us to interact with an LLM to generate the output given the provided tooling.
- `ReActAgent` is created with the custom tools (`poof_tool`, `shoop_tool`) and the LLM.

#### 3. Capturing Output

Using the `agent.chat` function, we can then call the agent with the prompt. We append "Use a tool to calculate every step" to prompt the LLM to use the provided tools from the agent. The agentic workflow is begun, and the process will continue until the entire alien math expression is evaluated.

```python
import io
import contextlib

# Capture verbose output
output_buffer = io.StringIO()
with contextlib.redirect_stdout(output_buffer):
    with st.spinner(text="Generating result..."):
        response = agent.chat(user + " Use a tool to calculate every step.")

# Format verbose output
verbose_output = output_buffer.getvalue()
```

---

https://docs.llamaindex.ai/en/stable/understanding/agent/basic_agent/

will have to implement custom LLM when product is ready: https://docs.llamaindex.ai/en/stable/module_guides/models/llms/usage_custom/