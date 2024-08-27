# Cerebras Inference API Demos

Welcome to the **Cerebras Inference API** demo repository! This repository contains various examples showcasing the power of the Cerebras Wafer-Scale Engines and CS-3 systems for AI model inference.

## 🚀 Introduction

The **Cerebras API** offers developers a low-latency solution for AI model inference powered by Cerebras Wafer-Scale Engines and CS-3 systems. We invite developers to explore the new possibilities that our high-speed inferencing solution unlocks.

Currently, the Cerebras API provides access to two models: Meta’s Llama 3.1 8B and 70B models. Both models are instruction-tuned and can be used for conversational applications.

### 🧠 Models Available

- **Llama-3.1-8B**
  - **Parameters**: 8 billion
  - **Knowledge Cutoff**: March 2023
  - **Context Length**: 8192
  - **Training Tokens**: 15 trillion

- **Llama-3.1-70B**
  - **Parameters**: 70 billion
  - **Knowledge Cutoff**: December 2023
  - **Context Length**: 8192
  - **Training Tokens**: 15 trillion

## 📚 Resources

- [Play with our live chatbot demo](https://inference.cerebras.ai/)
- [Experiment with our inference solution in the playground](https://cloud.cerebras.ai/)
- [Explore our API reference documentation](https://inference-docs.cerebras.ai/api-reference/chat-completions)

## 📁 Projects Overview

This repository contains multiple example projects, each demonstrating different capabilities of the Cerebras Inference API. Each project is located in its own folder and contains a detailed README.

### 🔗 Example Projects

- **[Getting Started with Cerebras Inference API](./getting-started/README.md)**
  - Learn how to get started with the Cerebras Inference API for your AI projects.

- **[Conversational Memory with Langchain](./conversational-memory-langchain/README.md)**
  - Explore how to build conversational memory for LLMs using Langchain.

- **[RAG with Pinecone + Docker](./rag-pinecone-docker/README.md)**
  - Implement Retrieval-Augmented Generation (RAG) using Pinecone and Docker.

- **[RAG with Weaviate + HuggingFace](./rag-weaviate-huggingface/README.md)**
  - Implement Retrieval-Augmented Generation (RAG) using Weaviate and HuggingFace.

- **[Getting Started with Cerebras + Streamlit](./cerebras-streamlit/README.md)**
  - Learn how to integrate Cerebras with Streamlit to build interactive applications.

- **[AI Agentic Workflow with LlamaIndex](./ai-workflow-llamaindex/README.md)**
  - Build an AI agentic workflow using LlamaIndex.

- **[AI Agentic Workflow with Langchain](./ai-workflow-langchain/README.md)**
  - Build an AI agentic workflow using Langchain.

- **[Multi AI Agentic Workflow](./multi-ai-workflow/README.md)**
  - Create a multi-agentic AI workflow with Langgraph and LangSmith.

---

## 🌟 Getting Started

To explore each project, simply navigate to the corresponding folder and follow the instructions in the README. Happy coding!

## 🛠️ Requirements

- Python 3.7+
- Docker (for RAG examples)
- Streamlit (for Cerebras + Streamlit example)
- Other dependencies as noted in each project’s README.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## 👥 Contributors

We welcome contributions! Feel free to submit a pull request or open an issue.

---

© 2024 Cerebras Systems
