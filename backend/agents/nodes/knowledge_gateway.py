import time
from agents.state import FINALSTATE, KnowledgeGatewayOutput

async def knowledge_gateway_node(state: FINALSTATE):
    start = time.time()
    rm_out = state.get("retrieval_manager_output")
    
    if not rm_out or rm_out.total_sources_gathered == 0:
        return {"knowledge_gateway_output": KnowledgeGatewayOutput(
            cleaned_context="No retrieval evidence gathered.",
            key_entities=[],
            summary="No evidence."
        )}
        
    print("Knowledge Gateway: Cleaning and formatting evidence...")
    
    all_contexts = []
    
    if rm_out.pdf_contexts:
        all_contexts.append("=== INTERNAL DOCUMENTS ===")
        all_contexts.extend(rm_out.pdf_contexts)
        
    if rm_out.web_contexts:
        all_contexts.append("=== WEB SEARCH ===")
        seen = set()
        for ctx in rm_out.web_contexts:
            if ctx not in seen:
                all_contexts.append(ctx)
                seen.add(ctx)
                
    cleaned_text = "\n\n".join(all_contexts)
    
    print(f"Knowledge Gateway processed in {time.time()-start:.2f}s")
    
    return {
        "knowledge_gateway_output": KnowledgeGatewayOutput(
            cleaned_context=cleaned_text,
            key_entities=[],
            summary=f"Gathered {rm_out.total_sources_gathered} sources."
        )
    }
