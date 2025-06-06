import streamlit as st
import os
from dotenv import load_dotenv
import time

from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFDirectoryLoader

# Load environment variables
load_dotenv()
os.environ['GROQ_API_KEY'] = os.getenv("GROQ_API_KEY")
os.environ['HF_TOKEN'] = os.getenv("HF_TOKEN")  # If needed for HuggingFace

# Initialize LLM (Groq with Llama3)
llm = ChatGroq(groq_api_key=os.environ['GROQ_API_KEY'], model_name="Llama3-8b-8192")

# Prompt template
prompt = ChatPromptTemplate.from_template(
    """
    Answer the questions based on the provided context only.
    Provide the most accurate response based on the question.
    <context>
    {context}
    <context>
    Question: {input}
    """
)

# Vector embedding function using HuggingFace (Free)
def create_vector_embedding():
    if "vectors" not in st.session_state:
        st.session_state.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        st.session_state.loader = PyPDFDirectoryLoader("research_papers")
        st.session_state.docs = st.session_state.loader.load()
        st.session_state.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        st.session_state.final_documents = st.session_state.text_splitter.split_documents(st.session_state.docs[:50])
        st.session_state.vectors = FAISS.from_documents(st.session_state.final_documents, st.session_state.embeddings)

# Streamlit UI
st.title("RAG Document Q&A With Groq (Llama3) and HuggingFace Embeddings")

user_prompt = st.text_input("Enter your query from the research paper")

if st.button("Create Document Embedding"):
    create_vector_embedding()
    st.success("Vector database is ready!")

if user_prompt:
    if "vectors" not in st.session_state:
        st.warning("Please click 'Create Document Embedding' first.")
    else:
        document_chain = create_stuff_documents_chain(llm, prompt)
        retriever = st.session_state.vectors.as_retriever()
        retrieval_chain = create_retrieval_chain(retriever, document_chain)

        start = time.process_time()
        response = retrieval_chain.invoke({'input': user_prompt})
        st.write("Answer:", response['answer'])
        st.caption(f"Response Time: {round(time.process_time() - start, 2)}s")

        with st.expander("Document similarity context"):
            for i, doc in enumerate(response['context']):
                st.write(doc.page_content)
                st.write('------------------------')
