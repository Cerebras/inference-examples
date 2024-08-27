import os
import streamlit as st
import weaviate
from langchain_weaviate import WeaviateVectorStore
from langchain_cerebras import ChatCerebras
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.question_answering import load_qa_chain
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings

# Function to upload vectors to Weaviate
def upload_vectors(texts, embeddings, progress_bar, cilent):
    vector_store = WeaviateVectorStore(client=client, index_name="my_class", text_key="text", embedding=embeddings)
    for i in range(len(texts)):
        t = texts[i]
        vector_store.add_texts([t.page_content])
        progress_bar.progress((i + 1) / len(texts), "Indexing PDF content... (this may take a bit) 🦙")

    progress_bar.empty()

    return vector_store

st.set_page_config(page_icon="🤖", layout="wide", page_title="Cerebras")
st.subheader("PDF Q&A with Weaviate 📄", divider="orange", anchor=False)

# Load secrets
with st.sidebar:
    st.link_button("Get Cerebras API key", "https://inference.cerebras.ai/")
    st.title("Settings")
    st.markdown("### :red[Enter your Cerebras API Key below]")
    CEREBRAS_API_KEY = st.text_input("Cerebras API Key:", type="password")
    st.markdown("### :red[Enter your Weaviate URL below]")
    WEAVIATE_URL = st.text_input("Weaviate URL:", type="password")
    st.markdown("### :red[Enter your Weaviate API Key below]")
    WEAVIATE_API_KEY = st.text_input("Weaviate API Key:", type="password")

if not CEREBRAS_API_KEY or not WEAVIATE_URL or not WEAVIATE_API_KEY:
    st.markdown("""
    ## Welcome to Cerebras x Weaviate Demo!

    This PDF analysis tool receives a file and allows you to ask questions about the content of the PDF through vector storage with Weaviate and a custom LLM implementation with Cerebras.

    To get started:
    1. :red[Enter your Cerebras and Weaviate API credentials in the sidebar.]
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
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000,
                                                   chunk_overlap=0)
    texts = text_splitter.split_documents(data)

    # Create embeddings
    with st.spinner(text="Loading embeddings..."):
        embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

    # Create a Weaviate client
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=WEAVIATE_URL,  # Replace with your Weaviate Cloud URL
        auth_credentials=weaviate.AuthApiKey(WEAVIATE_API_KEY),
    )

    # If the uploaded file is different from the previous one, update the index
    if uploaded_file.name != st.session_state.uploaded_pdf:
        st.session_state.uploaded_pdf = uploaded_file.name
        progress_bar = st.progress(0, text="Indexing PDF content... (this may take a bit)")
        st.session_state.docsearch = upload_vectors(texts, embeddings, progress_bar, client)
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
            st.session_state.messages.append({
                "role": "assistant",
                "content": response
            })
            st.markdown(response)