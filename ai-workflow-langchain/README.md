## Agentic Workflows for a Fifth Grader: An example with LangChain

This tutorial outlines the setup, code structure, and the implementation of a simple agentic workflow using Cerebras and LangChain.

<!-- ![finished product](./alienMath.png) -->

### Step 1: Set up your API Keys

1. **Obtain Your API Keys**: Log in to your Cerebras account, navigate to the “API Keys” section, and generate a new API key. Log in to your [LangChain account](https://smith.langchain.com) and click on the settings cog in the bottom left corner to generate a new API key.

2. **Set the API Key in the Sidebar**: Once you have the Cerebras and LangChain API keys, add them to the sidebar on the left.

### Step 2: Install the Cerebras Inference Library

You need to install the Cerebras Inference library to interact with the API. Use the following command to install the library along with other dependencies:

```bash
pip install https://cerebras-cloud-sdk.s3.us-west-1.amazonaws.com/test/cerebras_cloud_sdk-0.5.0-py3-none-any.whl
pip install -r requirements.txt
```

### Step 3: Start helping out a fellow fifth grader

Run the command `streamlit run main.py` to start up the frontend.

### What is an agentic workflow?
Within the context of LangChain, an agent is a software component driven by a large language model (LLM). It's assigned a task performs a sequence of actions to achieve it.

An "tool calling agent" in LangChain uses a set of tools to evaluate this task. **In this example, we'll be creating custom `multiply`, `add`, and `exponentiate` tools to solve word math problems.**

The agent evaluates these tools to determine the most effective one for each step. Once a step is completed, the agent assesses whether the task is finished and, if so, delivers the result to the user. If the task is not yet complete, the agent returns to the beginning of the process to continue with the next step. **You can see this workflow in action from the output of your request.**

### Code Overview

#### 1. Define Basic Tools

Before we do anything, we must load a prompt template for the agent to use when calling the LLM.

```python
# Get the prompt to use - can be replaced with any prompt that includes variables "agent_scratchpad" and "input"!
prompt = hub.pull("hwchase17/openai-tools-agent")
```

The custom `multiply`, `add`, and `exponentiate` tools are defined as shown below.

```python
from langchain import hub
from langchain_core.tools import tool

@tool
def multiply(first_int: int, second_int: int) -> int:
    """Multiply two integers together."""
    return first_int * second_int

@tool
def add(first_int: int, second_int: int) -> int:
    """Add two integers."""
    return first_int + second_int

@tool
def exponentiate(base: int, exponent: int) -> int:
    """Exponentiate the base to the exponent power."""
    return base**exponent
```

### 2. Processing User Input and Creating the Agent

The application collects user input for the word math problem:

```python
user = st.text_input("")
st.info("ex: Take 3 to the fifth power and multiply that by the sum of twelve and three, then square the whole result!")
```

We then initialize the LLM that will be constructing the final response.

```python
llm = ChatOpenAI(model="gpt-3.5-turbo-0125", api_key=api_key)
```

Passing in the LLM, tools, and the user's prompt, we can initialize an agent that can be used as a LangChain Runnable object that we will use to start the workflow.

```python
from langchain.agents import AgentExecutor, create_tool_calling_agent

# Construct the tool calling agent
agent = create_tool_calling_agent(llm, tools, prompt)
# Create an agent executor by passing in the agent and tools
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
```

#### 3. Capturing Output

By invoking the `agent_executor`, we can then call the agent with the prompt. The agentic workflow is begun, and the process will continue until the entire word math problem is evaluated.

```python
```python
result = agent_executor.invoke(
    {
        "input": user
    }
)
```

Read more from [LangChain's blog](https://python.langchain.com/v0.1/docs/use_cases/tool_use/quickstart/#agents).