import os
import streamlit as st
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.question_answering import load_qa_chain
from pinecone import Pinecone
from pinecone import ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_community.embeddings import OllamaEmbeddings
from langchain_cerebras import ChatCerebras

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
        llm = ChatCerebras(api_key=CEREBRAS_API_KEY, model="llama3.1-8b")
        chain = load_qa_chain(llm, chain_type="stuff")

        # Query the documents and get the answer
        response = chain.run(input_documents=docs, question=prompt)

        with st.chat_message("assistant", avatar="🤖"):
            # Save response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.markdown(response)