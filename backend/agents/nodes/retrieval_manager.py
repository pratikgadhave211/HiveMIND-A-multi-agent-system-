import time
from agents.state import FINALSTATE, RetrievalManagerOutput
from agents.rag import retrieve_with_hyde

async def retrieval_manager_node(state: FINALSTATE):
    start = time.time()
    query = state.get("user_query", "")
    
    print("Retrieval Manager: Performing local RAG retrieval...")
    
    pdf_contexts = []
    try:
        pdf_contexts = await retrieve_with_hyde(query, k=5)
    except Exception as e:
        print(f"RAG retrieval failed: {e}")
        
    total_sources = len(pdf_contexts)
    print(f"Retrieval Manager gathered {total_sources} sources from RAG in {time.time()-start:.2f}s")
    
    return {
        "retrieval_manager_output": RetrievalManagerOutput(
            query=query,
            pdf_contexts=pdf_contexts,
            web_contexts=[],
            total_sources_gathered=total_sources
        )
    }
