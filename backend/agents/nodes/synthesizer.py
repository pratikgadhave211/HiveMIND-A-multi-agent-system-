import time
from agents.state import FINALSTATE
from core.llm import llm

async def synthesizer_node(state: FINALSTATE):
    start = time.time()
    query = state.get("user_query", "")
    reranked_chunks = state.get("reranked_chunks", [])
    
    rm_out = state.get("retrieval_manager_output")
    pdf_contexts = rm_out.pdf_contexts if rm_out else []
    
    kg_output = state.get("knowledge_gateway_output")
    kg_context = kg_output.cleaned_context if kg_output and kg_output.cleaned_context else ""

    context_text = "\n\n".join([
        f"Source: {c.source_url}\nContent:\n{c.content}"
        for c in reranked_chunks
    ])
    
    # If kg_context doesn't exist (bypassed), use pdf_contexts directly
    local_evidence = kg_context
    if not local_evidence and pdf_contexts:
        local_evidence = "\n\n".join(pdf_contexts)
    
    if local_evidence:
        if context_text:
            context_text = f"=== PRE-ORCHESTRATION EVIDENCE (RAG) ===\n{local_evidence}\n\n=== POST-ORCHESTRATION EVIDENCE (WEB) ===\n{context_text}"
        else:
            context_text = f"=== PRE-ORCHESTRATION EVIDENCE (RAG) ===\n{local_evidence}"
            
    if not context_text.strip():
        return {"synthesized_context": "No relevant context found."}
    
    prompt = f"""
You are an expert information synthesizer.
The user's query is: "{query}"

Here is the gathered evidence (from pre-orchestration quick search/RAG and post-orchestration deep search):
{context_text}

Your task is to synthesize this information into a cohesive, highly dense, and organized "best context" summary. 
Filter out redundant noise and focus strictly on facts, data, quotes, and relevant details that answer the query.
Organize the information logically so the final report generator can easily consume it.
Do not write the final report, just write the synthesized context.
"""
    
    try:
        response = await llm.ainvoke(prompt)
        synthesized_context = response.content if hasattr(response, 'content') else str(response)
    except Exception as e:
        print(f"Synthesizer failed: {e}")
        synthesized_context = context_text  # fallback to raw chunks
        
    print(f"Synthesizer created context of {len(synthesized_context)} characters in {time.time()-start:.2f}s")
    
    return {"synthesized_context": synthesized_context}
