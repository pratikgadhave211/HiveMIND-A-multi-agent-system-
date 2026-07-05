import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from core.llm import model as hyde_llm  # deepseek-v4-pro

# Global vector store instance (in-memory for now)
vector_store = None
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")

def process_pdf(file_path: str):
    global vector_store
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(docs)
    
    if vector_store is None:
        vector_store = FAISS.from_documents(chunks, embeddings)
    else:
        vector_store.add_documents(chunks)
    
    return len(chunks)

def has_documents() -> bool:
    global vector_store
    return vector_store is not None

async def retrieve_with_hyde(query: str, k: int = 5) -> list[str]:
    global vector_store
    if vector_store is None:
        return []
        
    hyde_prompt = PromptTemplate.from_template(
        "Please write a hypothetical, highly detailed passage that perfectly answers the following query.\n\nQuery: {query}\n\nPassage:"
    )
    
    # Generate hypothetical document
    messages = hyde_prompt.format_prompt(query=query).to_messages()
    try:
        import asyncio
        # Add a 10-second timeout to prevent the pipeline from hanging
        response = await asyncio.wait_for(hyde_llm.ainvoke(messages), timeout=10.0)
        hypothetical_doc = response.content if hasattr(response, 'content') else str(response)
    except Exception as e:
        print(f"HyDE generation failed or timed out: {e}")
        hypothetical_doc = query # fallback to normal query if LLM fails
    
    # Search vector store using the hypothetical document
    docs = vector_store.similarity_search(hypothetical_doc, k=k)
    return [doc.page_content for doc in docs]
