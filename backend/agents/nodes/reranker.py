import time
from agents.state import FINALSTATE
from sentence_transformers import CrossEncoder

# Load the CrossEncoder model (using a fast, capable model for passage ranking)
cross_encoder_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2', max_length=512)

async def reranker_node(state: FINALSTATE):
    start = time.time()
    query = state.get("user_query", "")
    chunks = state.get("chunks", [])
    
    if not chunks or not query:
        return {"reranked_chunks": []}
    
    # Create pairs of [query, document_chunk]
    pairs = [[query, chunk.content] for chunk in chunks]
    
    import asyncio
    # Predict relevance scores (these are logits) in a separate thread to prevent event loop blocking
    scores = await asyncio.to_thread(cross_encoder_model.predict, pairs)
    
    # Assign scores back to chunks
    for chunk, score in zip(chunks, scores):
        chunk.relevance_score = float(score)
        
    # Sort chunks by their relevance score descending
    chunks.sort(key=lambda x: x.relevance_score, reverse=True)
    
    # Filter top chunks based on the top 30% of ranked chunks
    num_to_keep = max(3, int(len(chunks) * 0.30))  # Keep top 30%, but at least 3
    top_chunks = chunks[:num_to_keep]
    
    print(f"Reranker kept {len(top_chunks)} top chunks from {len(chunks)} in {time.time()-start:.2f}s")
    return {"reranked_chunks": top_chunks}
