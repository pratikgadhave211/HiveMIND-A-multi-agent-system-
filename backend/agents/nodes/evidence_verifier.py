import time
from agents.state import FINALSTATE

async def evidence_verifier_node(state: FINALSTATE):
    start = time.time()
    top_chunks = state.get("reranked_chunks", [])
    
    # Since we used the LLM for reranking, we consider them verified if they made it here.
    # Combine the top chunks into a format for the citation builder and synthesizer.
    
    verified_evidence = "\n\n".join([
        f"Source URL: {c.source_url}\nEvidence:\n{c.content}"
        for c in top_chunks
    ])
    
    print(f"Evidence Verifier combined {len(top_chunks)} chunks in {time.time()-start:.2f}s")
    
    # Overwrite fetched_content so that report.py uses this heavily filtered content.
    return {"fetched_content": verified_evidence}
