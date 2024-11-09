import os
import time
import random  # For adding randomness to backoff
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import Qdrant
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import streamlit as st

# Load environment variables
load_dotenv()

@st.cache_resource
def get_qdrant_client():
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    if not qdrant_url or not qdrant_api_key:
        st.error("QDRANT_URL or QDRANT_API_KEY is not set in the environment variables.")
        return None
    try:
        client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key, timeout=60)  # Set timeout
        collections = client.get_collections()
        st.write(f"Connected to Qdrant. Existing collections: {collections}")
        return client
    except Exception as e:
        st.error(f"Failed to connect to Qdrant: {str(e)}")
        return None

@st.cache_resource
def process_pdf_folder(pdf_folder):
    client = get_qdrant_client()
    if client is None:
        raise ValueError("Failed to initialize Qdrant client. Check environment variables and Qdrant settings.")

    collection_name = "Homecarepdf_1731152491"
    st.write(f"Attempting to create collection with name: {collection_name}")
    
    try:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE),
        )
        st.write(f"Collection '{collection_name}' created successfully.")
    except Exception as e:
        st.error(f"Failed to create collection '{collection_name}': {str(e)}")
        return None
    
    try:
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        vector_store = Qdrant(client=client, collection_name=collection_name, embeddings=embeddings)
    except Exception as e:
        st.error(f"Failed to initialize vector store: {str(e)}")
        return None

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    batch_size = 100

    for file_name in os.listdir(pdf_folder):
        file_path = os.path.join(pdf_folder, file_name)
        if file_path.endswith(".pdf"):
            try:
                st.write(f"Processing file: {file_name}")
                loader = PyPDFLoader(file_path)
                documents = loader.load()
                texts = text_splitter.split_documents(documents)

                for i in range(0, len(texts), batch_size):
                    batch = texts[i:i+batch_size]
                    attempt, max_retries, success = 0, 5, False
                    while attempt < max_retries and not success:
                        try:
                            vector_store.add_documents(batch)
                            st.write(f"Added batch {i//batch_size + 1} for file {file_name}")
                            success = True
                        except Exception as e:
                            st.error(f"Error adding batch for file {file_name}: {str(e)}")
                            if "quota" in str(e).lower() or "429" in str(e):
                                wait_time = (2 ** attempt) + random.uniform(0, 1)
                                st.write(f"Retrying in {wait_time:.2f} seconds...")
                                time.sleep(wait_time)
                                attempt += 1
                            else:
                                break  # Exit retry loop for non-rate-limit errors

            except Exception as e:
                st.error(f"Error processing {file_name}: {str(e)}")
    
    st.success(f"All PDFs processed successfully! Created collection: {collection_name}")
    return vector_store, collection_name

# # Usage example
# pdf_folder_path = "/Users/hemantgoyal/Downloads/Freelancing/Active Clients/Roshan/Home owner Helper/pdf"
# process_pdf_folder(pdf_folder_path)
