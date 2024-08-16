## Three's the Charm: Multi Agentic Workflow with LangChain and LangGraph

This tutorial outlines how to build a three-agent workflow (researcher, editor, and writer) that produces a blog utilizing LangChain, LangGraph, and the Cererbras API.

<!-- ![finished product](./alienMath.png) -->

### Step 1: Set up your API Keys

1. **Obtain Your API Keys**:
* Log in to your Cerebras account, navigate to the “API Keys” section, and generate a new API key.
* Do the same with the [Tavily API](https://app.tavily.com/home).
* Finally, log in to your [LangChain account](https://smith.langchain.com) and click on the settings cog in the bottom left corner to generate a new API key.

2. **Set the API Keys in the Sidebar**: Once you have the Cerebras, Tavily, & LangChain API keys, add them to the sidebar on the left.

### Step 2: Install the Cerebras Inference Library

You need to install the Cerebras Inference library to interact with the API. Use the following command to install the library along with other dependencies:

```bash
pip install https://cerebras-cloud-sdk.s3.us-west-1.amazonaws.com/test/cerebras_cloud_sdk-0.5.0-py3-none-any.whl
pip install -r requirements.txt
```

### Step 3: Start your App

Run the command `streamlit run main.py` to start up the frontend.

---

https://medium.com/indiciumtech/how-to-build-a-multi-agent-content-development-team-using-langgraph-d062ce4051c3