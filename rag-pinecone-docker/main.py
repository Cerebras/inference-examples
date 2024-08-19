import os
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.question_answering import load_qa_chain
from pinecone import Pinecone
from pinecone import ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_community.embeddings import OllamaEmbeddings

# Importing dependencies for custom LLM implementation
from cerebras.cloud.sdk import Cerebras
from typing import Any, List, Optional
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models.llms import LLM
from langchain_community.embeddings import OllamaEmbeddings

import streamlit as st

class CerebrasLLM(LLM):
  """A custom LLM implementation for the Cerebras API."""

  api_key: str
  model_name: str

  def _call(
      self,
      prompt: str,
      stop: Optional[List[str]] = None,
      run_manager: Optional[CallbackManagerForLLMRun] = None,
      **kwargs: Any,
  ) -> str:
      if stop is not None:
          raise ValueError("stop kwargs are not permitted.")

      # Create a completion request to the Cerebras API
      user_message = {"role": "user", "content": prompt}
      response = Cerebras(api_key=self.api_key).chat.completions.create(
          messages=[user_message],
          model=self.model_name,
          **kwargs
      )

      # Calculate tokens per second
      total_tokens = response.usage.total_tokens
      total_time = response.time_info.total_time
      tokens_per_second = total_tokens / total_time

      # Extract and return the text from the response along with metric
      return response.choices[0].message.content + f"\n(Tokens per second: {tokens_per_second:.2f})"

  @property
  def _llm_type(self) -> str:
      """Get the type of language model used by this chat model. Used for logging purposes only."""
      return "cerebras"

# Function to upload vectors to Pinecone
def upload_vectors(texts, embeddings, index_name, progress_bar):
    vector_store = PineconeVectorStore(index_name=index_name, embedding=embeddings)
    for i in range(len(texts)):
        t = texts[i]
        vector_store.add_texts([t.page_content])
        progress_bar.progress((i + 1) / len(texts), "Indexing PDF content... (this may take a bit) 🦙")

    progress_bar.empty()

    return vector_store
  
st.set_page_config(page_icon="🤖", layout="wide",
    page_title="Cerebras")
st.subheader("PDF Q&A with Pinecone & Ollama 📄", divider="orange", anchor=False)

# Load secrets
with st.sidebar:
    st.title("Settings")
    st.markdown("### :red[Enter your Cerebras API Key below]")
    CEREBRAS_API_KEY = st.text_input("Cerebras API Key:", type="password")
    st.markdown("### :red[Enter your Pinecone API Key below]")
    os.environ["PINECONE_API_KEY"] = st.text_input("Pinecone API Key:", type="password")

if not CEREBRAS_API_KEY or not os.environ["PINECONE_API_KEY"]:
    st.markdown("""
    ## Welcome to Cerebras x Pinecone x Ollama Demo!

    This PDF analysis tool receives a file and allows you to ask questions about the content of the PDF through vector storage with Pinecone, embeddings with Ollama, and a custom LLM implementation with Cerebras.

    To get started:
    1. :red[Enter your Cerebras and Pinecone API Keys in the sidebar.]
    2. Upload a PDF file to analyze.
    3. Was the PDF TLDR? Ask a question!

    """)

    st.stop()

# Initialize chat history and selected model
if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_pdf" not in st.session_state:
    st.session_state.uploaded_pdf = None

if "docsearch" not in st.session_state:
    st.session_state.docsearch = None
    
index_name = "python-index"

# Load the PDF data
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

st.divider()

# Display chat messages stored in history on app rerun
for message in st.session_state.messages:
    avatar = '🤖' if message["role"] == "assistant" else '❔'
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# If a file is uploaded, process it
if uploaded_file is None:
    st.markdown("Please upload a PDF file.")
else:
    temp_filepath = os.path.join("/tmp", uploaded_file.name)
    with open(temp_filepath, "wb") as f:
        f.write(uploaded_file.getvalue())

    loader = PyPDFLoader(temp_filepath)
    data = loader.load()

    # Split the data into smaller documents
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.split_documents(data)

    # Create embeddings
    embeddings = OllamaEmbeddings(model="nomic-embed-text")

    # Create a Pinecone index and add the documents to it
    pc = Pinecone()

    # Create the index if it does not exist
    if index_name not in pc.list_indexes().names():
        with st.spinner(text="Creating Pinecone index..."):
            pc.create_index(
                name=index_name, 
                dimension=768, # output dimension of nomic-embed-text
                metric="cosine",
                spec=ServerlessSpec(
                    cloud='aws', 
                    region='us-east-1'
                )
    )
    
    # If the uploaded file is different from the previous one, update the index
    if uploaded_file.name != st.session_state.uploaded_pdf:
        st.session_state.uploaded_pdf = uploaded_file.name
        progress_bar = st.progress(0, text="Indexing PDF content... (this may take a bit) 🦙")
        st.session_state.docsearch = upload_vectors(texts, embeddings, index_name, progress_bar)
        st.session_state.messages = []
        

    # Get user input
    if prompt := st.chat_input("Enter your prompt here..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar='❔'):
            st.markdown(prompt)

        # Perform similarity search
        docs = st.session_state.docsearch.similarity_search(prompt)

        # Load the question answering chain
        llm = CerebrasLLM(api_key=CEREBRAS_API_KEY, model_name="llama3.1-8b")
        chain = load_qa_chain(llm, chain_type="stuff")

        # Query the documents and get the answer
        response = chain.run(input_documents=docs, question=prompt)

        with st.chat_message("assistant", avatar="🤖"):
            # Save response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.markdown(response)