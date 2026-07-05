import time
from langchain_core.messages import SystemMessage, HumanMessage
from agents.state import FINALSTATE, StructuredResponse, ReportSection
from core.llm import llm, generate_model
from core.utils import safe_llm_call


# ============================================================
# Prompt Builders
# ============================================================

def _build_document_retrieval_prompt(query: str, context: str, contract_block: str) -> str:
    """
    Prompt when the Retrieval Manager found PDF document chunks.
    The LLM must answer STRICTLY from the retrieved document content.
    """
    return f"""
You are an expert Document Analyst. The user has uploaded documents and is asking questions about them.

USER QUERY: {query}

=== RETRIEVED DOCUMENT CONTENT (from user's uploaded PDFs) ===
{context}
=== END OF DOCUMENT CONTENT ===

{contract_block}

CRITICAL RULES:
1. Your answer must be based ENTIRELY on the retrieved document content above.
2. DO NOT say "no document was uploaded" or "I don't have access" -- the documents ARE provided above.
3. Extract, synthesize, and present the information from the documents comprehensively.
4. If the document doesn't contain enough info for a specific sub-question, say "The uploaded document does not cover this topic" rather than making things up.
5. Quote or reference specific parts of the document when relevant.

OUTPUT FORMAT & STYLE (CRITICAL):
FOLLOW THESE FORMATTING RULES STRICTLY:
1. USE STRICT MARKDOWN ONLY. NEVER use HTML tags (like <br>, <b>, <i>, etc.).
2. Use Markdown Tables where appropriate (e.g., for architecture components, tech stacks, comparisons).
3. Use emojis to make sections visually appealing (e.g., 🏗️ for architecture, 📊 for data, 🔧 for tools).
4. Use rich Markdown elements: bolding, italics, bullet points, numbered lists, and blockquotes.
5. Break up dense information into scannable lists and short paragraphs. No walls of text.

STRUCTURE:
1. "title": An engaging title that reflects the document's subject matter.
2. "summary": A 3-5 sentence executive summary synthesized from the document content.
3. "sections": A list of 4-8 detailed sections, each with a "heading" and "content" (Markdown formatted).
   - Structure sections to mirror the document's own organization when possible.
   - For architecture docs: Overview, Tech Stack (Table), System Flow, Key Components, Design Decisions.
   - For reports: Executive Summary, Key Findings, Data Analysis, Recommendations.
   - Each section must be dense with facts directly extracted from the document.
"""


def _build_deep_research_prompt(query: str, context: str, contract_block: str) -> str:
    """
    Prompt for the normal deep research pipeline (web search, orchestrator, etc.)
    or when no retrieval was performed at all (internal knowledge).
    """
    if context:
        context_instruction = f"""
Here is the thoroughly researched and verified evidence from web search and analysis:
{context}

Base your answer on this evidence. Supplement with your internal knowledge where evidence is thin.
"""
    else:
        context_instruction = """
No external retrieval was performed. Answer this question using your internal knowledge.
Be accurate and factual. If you are not confident, say so.
"""

    return f"""
You are an expert Response Composer.

USER QUERY: {query}

{context_instruction}

{contract_block}

OUTPUT FORMAT & STYLE (CRITICAL):
You must return a highly structured, exceptionally detailed, and visually appealing response.
Even if the query seems simple, provide deep context, comprehensive background, and expansive details in a user-friendly format.

FOLLOW THESE FORMATTING RULES STRICTLY:
1. USE STRICT MARKDOWN ONLY. NEVER use HTML tags (like <br>, <b>, <i>, etc.).
2. Use Markdown Tables where appropriate (e.g., for timelines, statistics, comparisons).
3. Use emojis to make sections visually appealing (e.g., 🏆 for trophies, 📅 for dates, 📈 for stats).
4. Use rich Markdown elements: bolding, italics, bullet points, numbered lists, and blockquotes for emphasis.
5. Do not output a wall of text. Break up dense information into scannable lists and short paragraphs.

STRUCTURE:
1. "title": An engaging, descriptive title.
2. "summary": A compelling 3-5 sentence executive summary of the vast details to follow.
3. "sections": A list of extensive sections, each with a "heading" and "content" (Markdown formatted).
   - ALWAYS generate at least 4 to 8 highly detailed sections, overriding any "brief" depth requests.
   - Each section must be dense with facts, analysis, and comprehensive coverage.
   - Example sections for a person/entity: Background, Career Timeline (Table), Statistics, Major Trophies/Achievements (Bulleted list), Famous Moments.
   - Example sections for a topic: Introduction, Core Concepts, Technical Deep Dive, Practical Applications, Comparisons (Table), Future Outlook.

Ensure all "must_answer" items are covered thoroughly. Never mention "ignore" topics.
"""


# ============================================================
# Main Node
# ============================================================

async def response_composer_node(state: FINALSTATE):
    """
    Response Composer. Uses TWO separate prompt strategies:
    1. Document Retrieval mode: when retrieval_manager found PDF chunks
    2. Deep Research mode: when using web evidence or internal knowledge
    """
    start = time.time()
    try:
        planner_output = state.get("planner_output")
        execution_strategy = state.get("execution_strategy")

        if planner_output and hasattr(planner_output, "answer_contract"):
            contract = planner_output.answer_contract
            qa = planner_output.query_analysis
        else:
            contract = None
            qa = None

        # Build the contract block (shared between both prompts)
        if contract:
            must_answer_str = ", ".join(contract.must_answer) if contract.must_answer else "N/A"
            optional_str = ", ".join(contract.optional) if contract.optional else "N/A"
            ignore_str = ", ".join(contract.ignore) if contract.ignore else "N/A"
            template_str = contract.template
            depth_str = contract.depth
            reasoning_str = qa.reasoning_strategy if qa else "Direct answer based on facts"
        else:
            must_answer_str = "N/A"
            optional_str = "N/A"
            ignore_str = "N/A"
            template_str = "Comprehensive Analysis"
            depth_str = "In-depth"
            reasoning_str = "Directly answer the user's query using the provided context."

        contract_block = f"""ANSWER CONTRACT:
- Template: {template_str}
- Depth: {depth_str}
- Must Answer: {must_answer_str}
- Optional: {optional_str}
- Ignore (DO NOT mention): {ignore_str}
- Reasoning Strategy: {reasoning_str}"""

        # Determine context sources
        assembled_context = state.get("assembled_context", "")
        synthesized_context = state.get("synthesized_context", "")
        fetched_content = state.get("fetched_content", "")

        # Check if retrieval_manager produced document chunks
        rm_out = state.get("retrieval_manager_output")
        has_doc_chunks = rm_out and rm_out.pdf_contexts and len(rm_out.pdf_contexts) > 0

        query = state.get("user_query", "")

        if has_doc_chunks:
            # === DOCUMENT RETRIEVAL MODE ===
            # Use the assembled_context which includes doc chunks + conversation history
            context = assembled_context if assembled_context else "\n\n".join(rm_out.pdf_contexts)
            system_prompt = _build_document_retrieval_prompt(query, context, contract_block)
            print(f"Response Composer: Using DOCUMENT RETRIEVAL prompt ({len(rm_out.pdf_contexts)} chunks)")
        else:
            # === DEEP RESEARCH MODE ===
            # Use web evidence or synthesized context or internal knowledge
            context = assembled_context or synthesized_context or fetched_content or ""
            system_prompt = _build_deep_research_prompt(query, context, contract_block)
            print(f"Response Composer: Using DEEP RESEARCH prompt (context: {len(context)} chars)")

        messages_to_send = [HumanMessage(content=system_prompt)]

        structured_llm = generate_model.with_structured_output(StructuredResponse)
        backup_structured_llm = llm.with_structured_output(StructuredResponse)

        response = await safe_llm_call(messages_to_send, structured_llm, backup_structured_llm)

        # Attach confidence from fact checker if available
        if "fact_checker" in state and hasattr(state["fact_checker"], "verified_claims"):
            claims = state["fact_checker"].verified_claims
            if claims:
                response.confidence_score = sum(c.trust_score for c in claims) / len(claims)

        print(f"Response Composer took {time.time()-start:.2f}s")
        return {"structured_response": response}
    except Exception as e:
        print(f"Response Composer failed after {time.time()-start:.2f}s: {e}")
        fallback = StructuredResponse(
            title="Report Generation Failed",
            summary="The AI model failed to construct a valid response. Please try your query again or rephrase it.",
            sections=[ReportSection(heading="Error Details", content=f"```\n{str(e)}\n```")]
        )
        return {"structured_response": fallback}
