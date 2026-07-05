import time
from agents.state import FINALSTATE
from core.llm import tavily_client, llm, backup_model
from core.utils import safe_llm_call
from memory import chat_store, context_assembler
from agents.rag import has_documents, retrieve_with_hyde
import asyncio
from pydantic import BaseModel, Field


class FastRetrievalCheck(BaseModel):
    needs_retrieval: bool = Field(description="True if the query requires looking up live, dynamic, or external facts on the web. False for conversational, static, or math queries.")
    reason: str


# ============================================================
# Prompt Builders
# ============================================================

def _build_fast_document_prompt(query: str, doc_chunks: list[str], history_block: str) -> str:
    """
    Prompt when user has uploaded documents. Answer from the document chunks.
    """
    doc_context = "\n\n".join(doc_chunks[:8])
    return f"""
You are a fast Document Q&A assistant. The user has uploaded documents and is asking questions about them.

=== RETRIEVED DOCUMENT CONTENT (from user's uploaded PDFs) ===
{doc_context}
=== END OF DOCUMENT CONTENT ===
{history_block}

CRITICAL RULES:
1. Your answer must be based ENTIRELY on the retrieved document content above.
2. DO NOT say "no document was uploaded" or "I don't have access" -- the documents ARE provided above.
3. Extract and present the information clearly and concisely.
4. If the document doesn't cover a specific sub-question, say "The uploaded document does not cover this topic."

FORMATTING RULES:
1. USE STRICT MARKDOWN ONLY. NEVER use HTML tags (like <br>, <b>, <i>, etc.).
2. Use Markdown Tables, bullet points, bolding, and emojis where they improve readability.
3. Keep the response concise but informative -- this is a fast answer, not a full research report.

CURRENT USER QUERY:
{query}
"""


def _build_fast_web_prompt(query: str, web_context: str, history_block: str) -> str:
    """
    Prompt for fast web search or internal knowledge answers (no documents uploaded).
    """
    if web_context:
        context_instruction = f"Context from web search:\n{web_context}\n\nProvide a direct, concise, and accurate answer based on the provided context."
    else:
        context_instruction = "No web search was performed because it wasn't needed. Answer the user directly based on your internal knowledge."

    return f"""
You are a fast-response AI assistant.

{context_instruction}
{history_block}

FORMATTING RULES:
1. USE STRICT MARKDOWN ONLY. NEVER use HTML tags.
2. Use bullet points, bolding, tables, and emojis where they improve readability.
3. Keep the response concise and direct.

Please provide a direct, concise, and accurate answer to the user's CURRENT query below.
If the current query is conversational (like "hi" or "thanks"), respond appropriately.
If the user references something from the conversation history, use that context.

CURRENT USER QUERY:
{query}
"""


# ============================================================
# Main Node
# ============================================================

async def fast_search_agent_node(state: FINALSTATE):
    start = time.time()
    try:
        query = state['user_query']
        thread_id = state.get("_thread_id", "")

        fast_model = llm
        backup_fast_model = backup_model

        # Build conversation history block (shared between both paths)
        conversation_context = context_assembler.assemble_context(thread_id)
        history_block = ""
        if conversation_context:
            history_block = f"""
CONVERSATION CONTEXT (use this to understand references and maintain continuity):
{conversation_context}
"""

        # Check if documents are uploaded -- if so, use document retrieval path
        rm_out = state.get("retrieval_manager_output")
        has_doc_chunks = rm_out and rm_out.pdf_contexts and len(rm_out.pdf_contexts) > 0

        if has_doc_chunks:
            # === DOCUMENT MODE ===
            prompt = _build_fast_document_prompt(query, rm_out.pdf_contexts, history_block)
            print(f"Fast Search: Using DOCUMENT prompt ({len(rm_out.pdf_contexts)} chunks)")
        elif has_documents():
            # Documents exist but retrieval_manager didn't run (fast path skipped it)
            # Do a quick HyDE retrieval ourselves
            try:
                doc_chunks = await retrieve_with_hyde(query, k=5)
                if doc_chunks:
                    prompt = _build_fast_document_prompt(query, doc_chunks, history_block)
                    print(f"Fast Search: Using DOCUMENT prompt (direct HyDE, {len(doc_chunks)} chunks)")
                else:
                    raise ValueError("No chunks returned")
            except Exception:
                # Fallback to web search
                prompt = await _do_web_search_and_build_prompt(query, history_block, fast_model, backup_fast_model)
        else:
            # === NORMAL WEB/INTERNAL MODE ===
            prompt = await _do_web_search_and_build_prompt(query, history_block, fast_model, backup_fast_model)

        answer = await safe_llm_call(prompt, fast_model, backup_fast_model)

        print(f"Fast Search Agent took {time.time()-start:.2f}s")
        return {
            "final_report": answer.content if hasattr(answer, 'content') else answer,
        }
    except Exception as e:
        print(f"Fast Search Agent failed after {time.time()-start:.2f}s")
        raise


async def _do_web_search_and_build_prompt(query: str, history_block: str, fast_model, backup_fast_model) -> str:
    """Helper: decide if web search is needed, do it, and return the final prompt string."""
    check_prompt = f"""
You are a fast retrieval checker. Decide if we need to search the web to answer this user query.
USER QUERY: {query}
"""
    structured_llm = fast_model.with_structured_output(FastRetrievalCheck)
    backup_structured_llm = backup_fast_model.with_structured_output(FastRetrievalCheck)

    check = await safe_llm_call(check_prompt, structured_llm, backup_structured_llm)

    web_context = ""
    if check.needs_retrieval:
        response = await asyncio.to_thread(
            tavily_client.search,
            query=query,
            max_results=3,
            search_depth="advanced"
        )
        web_context = "\n\n".join([
            f"Title: {item['title']}\nURL: {item['url']}\nContent: {item['content']}"
            for item in response.get("results", [])
        ])
        print(f"Fast Search: Using WEB SEARCH prompt (retrieval=True)")
    else:
        print(f"Fast Search: Using INTERNAL KNOWLEDGE prompt (retrieval=False)")

    return _build_fast_web_prompt(query, web_context, history_block)
