"""
Query Rewriter — Coreference Resolution Node.
Resolves ambiguous references ("it", "that", "this", "the above") into
standalone questions using recent chat history. Runs BEFORE the intent router.
"""
import time
from agents.state import FINALSTATE, QueryRewriterOutput
from core.llm import llm, backup_model
from core.utils import safe_llm_call
from memory import chat_store


async def query_rewriter_node(state: FINALSTATE):
    """
    Rewrites the user query to resolve coreferences using recent chat history.
    If the query is already standalone, returns it unchanged.
    """
    start = time.time()
    query = state.get("user_query", "")
    thread_id = state.get("_thread_id", "")

    # Get last 5 turns for coreference context
    recent = chat_store.format_recent_turns(thread_id, n=5)

    # If no chat history, the query is already standalone
    if not recent:
        print(f"Query Rewriter: No history, passing through ({time.time()-start:.2f}s)")
        return {
            "rewritten_query": query,
            "query_rewriter_output": QueryRewriterOutput(
                original_query=query, rewritten_query=query, was_rewritten=False
            )
        }

    prompt = f"""You are a query rewriter. Your ONLY job is to resolve ambiguous references in the user's CURRENT query using the recent conversation history.

RECENT CONVERSATION:
{recent}

CURRENT USER QUERY: "{query}"

RULES:
1. If the query contains pronouns like "it", "its", "that", "this", "they", "them", "the above", "those", or references something from the conversation — rewrite it into a fully self-contained question.
2. If the query is ALREADY standalone and clear, return it EXACTLY as-is.
3. Do NOT add information the user didn't ask for. Only resolve references.
4. Return ONLY the rewritten query text. No explanations.

REWRITTEN QUERY:"""

    try:
        response = await safe_llm_call(prompt, llm, backup_model)
        rewritten = response.content.strip() if hasattr(response, 'content') else str(response).strip()
        # Remove surrounding quotes if the LLM added them
        rewritten = rewritten.strip('"').strip("'")
        was_rewritten = rewritten.lower() != query.lower()
    except Exception as e:
        print(f"Query Rewriter failed: {e}")
        rewritten = query
        was_rewritten = False

    if was_rewritten:
        print(f"Query Rewriter: '{query}' -> '{rewritten}' ({time.time()-start:.2f}s)")
    else:
        print(f"Query Rewriter: No rewrite needed ({time.time()-start:.2f}s)")

    return {
        "rewritten_query": rewritten,
        "user_query": rewritten,  # Override so downstream nodes use the resolved query
        "query_rewriter_output": QueryRewriterOutput(
            original_query=query,
            rewritten_query=rewritten,
            was_rewritten=was_rewritten,
        )
    }
