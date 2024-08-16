import os

from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
# from langchain.vectorstores import Pinecone
from langchain.chains.question_answering import load_qa_chain
from pinecone import Pinecone
from pinecone import ServerlessSpec
from langchain.vectorstores import Pinecone as PineconeVectorStore
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

st.set_page_config(page_icon="🤖", layout="wide",
    page_title="CerebrasLite")
st.subheader("Cerebras and a Llama (Ollama)", divider="orange", anchor=False)

# Initialize chat history and selected model
if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_pdf" not in st.session_state:
    st.session_state.uploaded_pdf = None

if "docsearch" not in st.session_state:
    st.session_state.docsearch = None
    
# Load secrets
CEREBRAS_API_KEY = os.environ.get('CEREBRAS_API_KEY')
PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
index_name = "python-index"

# Load the PDF data
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

st.divider()

# Display chat messages stored in history on app rerun
for message in st.session_state.messages:
    avatar = '🤖' if message["role"] == "assistant" else '❔'
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

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
    pc = Pinecone(
        api_key=PINECONE_API_KEY
    )

    # Create the index if it does not exist
    if index_name not in pc.list_indexes().names():
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
        st.session_state.docsearch = PineconeVectorStore.from_texts([t.page_content for t in texts], embeddings, index_name=index_name)
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
