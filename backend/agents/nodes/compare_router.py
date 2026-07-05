import time
from agents.state import FINALSTATE, CompareRouterOutput
from core.llm import llm, backup_model
from core.utils import safe_llm_call

async def compare_router_node(state: FINALSTATE):
    start = time.time()
    query = state.get("user_query", "")
    rm_out = state.get("retrieval_manager_output")
    
    pdf_contexts = rm_out.pdf_contexts if rm_out else []
    context_str = "\n\n".join(pdf_contexts)
    
    if not context_str:
        return {"compare_router_output": CompareRouterOutput(needs_web_search=True, research_topics="No local context found.")}
    
    prompt = f"""
You are an intelligent router deciding if a user's query can be fully answered using the provided local document context, or if additional web search is required.

USER QUERY: "{query}"

LOCAL DOCUMENT CONTEXT:
{context_str}

If the context contains enough information to comprehensively answer the user's query without needing any outside information, output needs_web_search=false.
If the context is insufficient, outdated, or the user specifically asks for external information (like recent news), output needs_web_search=true and specify the required research topics in 'research_topics'.

Return a valid JSON output matching the requested schema.
"""
    
    structured_llm = llm.with_structured_output(CompareRouterOutput)
    backup_structured_llm = backup_model.with_structured_output(CompareRouterOutput)
    
    print("Compare Router: Analyzing RAG context sufficiency...")
    try:
        result = await safe_llm_call(prompt, structured_llm, backup_structured_llm)
        print(f"Compare Router decision: needs_web_search={result.needs_web_search} (Time: {time.time()-start:.2f}s)")
        
        updates = {"compare_router_output": result}
        
        if result.needs_web_search and result.research_topics:
            updates["user_query"] = f"{query}\n\nAdditional topics to research based on document gaps: {result.research_topics}"
        else:
            # Bypass mode: send the RAG context directly to the response composer
            updates["synthesized_context"] = f"=== RAG DOCUMENT CONTEXT ===\n{context_str}"
            
        return updates
    except Exception as e:
        print(f"Compare router failed: {e}")
        return {"compare_router_output": CompareRouterOutput(needs_web_search=True, research_topics="Fallback due to LLM error")}
