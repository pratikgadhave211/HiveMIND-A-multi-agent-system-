"""
Query Router — Retrieval Source Selector Node.
Decides WHICH memory sources the current query needs to prevent retrieval contamination.
Routes to: docs_only, conversation_only, docs_and_web, web_only, no_retrieval
"""
import time
from agents.state import FINALSTATE, QueryRouterOutput
from agents.rag import has_documents
from core.llm import llm, backup_model
from core.utils import safe_llm_call
from memory import chat_store


async def query_router_node(state: FINALSTATE):
    """
    Analyzes the query and conversation context to decide which retrieval sources to use.
    This prevents retrieval contamination — e.g., don't search uploaded docs for news queries.
    """
    start = time.time()
    query = state.get("user_query", "")
    thread_id = state.get("_thread_id", "")
    execution_strategy = state.get("execution_strategy")

    docs_available = has_documents()
    recent_turns = chat_store.format_recent_turns(thread_id, n=3)

    # Build a concise context for the router
    context_info = []
    if docs_available:
        context_info.append("- User has uploaded documents (PDFs) available for retrieval")
    if recent_turns:
        context_info.append(f"- Recent conversation exists:\n{recent_turns}")
    context_block = "\n".join(context_info) if context_info else "No documents uploaded. No prior conversation."

    prompt = f"""You are a query router. Decide which retrieval sources are needed to answer the user's query.

AVAILABLE SOURCES:
1. docs_only — Search uploaded documents/PDFs only (use when query is about the uploaded content)
2. conversation_only — Use only conversation history (use when user asks about what was previously discussed)
3. docs_and_web — Search both documents AND the web (use when comparing document content with external info)
4. web_only — Search the web only (use for news, general knowledge, live data, etc.)
5. no_retrieval — No retrieval needed (use for greetings, simple math, opinions, conversational replies)

CURRENT CONTEXT:
{context_block}

USER QUERY: "{query}"

Choose the SINGLE best route. Return the route name and a brief reasoning.
"""

    structured_llm = llm.with_structured_output(QueryRouterOutput)
    backup_structured_llm = backup_model.with_structured_output(QueryRouterOutput)

    try:
        result = await safe_llm_call(prompt, structured_llm, backup_structured_llm)

        # Override: if no docs uploaded, never route to docs_only or docs_and_web
        if not docs_available and result.route in ("docs_only", "docs_and_web"):
            result = QueryRouterOutput(route="web_only", reasoning="No documents uploaded, falling back to web search.")

        print(f"Query Router: {result.route} — {result.reasoning} ({time.time()-start:.2f}s)")
        return {"query_router_output": result}
    except Exception as e:
        print(f"Query Router failed: {e}")
        # Sensible fallback: if docs exist, check both; otherwise web only
        fallback_route = "docs_and_web" if docs_available else "web_only"
        return {
            "query_router_output": QueryRouterOutput(
                route=fallback_route,
                reasoning=f"Fallback due to error: {str(e)[:80]}"
            )
        }
