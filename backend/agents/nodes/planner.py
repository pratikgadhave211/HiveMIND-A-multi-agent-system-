import time
from agents.state import FINALSTATE, AnswerContract, PlannerOutput, VerificationStrategy
from langchain_core.messages import SystemMessage, HumanMessage
from core.llm import llm, backup_model
from core.utils import safe_llm_call

async def answer_contract_builder_node(state: FINALSTATE):
    """
    Step 3 of the semantic pipeline.
    Combines QueryAnalysis + KnowledgeAnalysis and builds the AnswerContract + VerificationStrategy.
    Produces the final PlannerOutput — a complete semantic understanding of the request.
    """
    start = time.time()
    try:
        query_analysis = state["query_analysis_result"]
        knowledge_analysis = state["knowledge_analysis_result"]

        # Build Verification Strategy deterministically
        verification = VerificationStrategy(required=False, confidence_target=0.8)
        if knowledge_analysis.knowledge_type in ("dynamic", "live"):
            verification.required = True
            verification.confidence_target = 0.9
        if knowledge_analysis.volatility in ("high", "extreme"):
            verification.confidence_target = 0.95
        if query_analysis.domain in ("finance", "medical", "legal"):
            verification.required = True
            verification.confidence_target = 0.95


        system_prompt = f"""
You are an Answer Contract Builder. Given the user's query and its analysis, define the shape of the ideal answer.
You must NEVER reference tools, APIs, search engines, or agents.

QUERY ANALYSIS:
- Intent: {query_analysis.intent}
- Domain: {query_analysis.domain}
- Query Type: {query_analysis.query_type}
- Complexity: {query_analysis.complexity}
- Reasoning Strategy: {query_analysis.reasoning_strategy}

KNOWLEDGE ANALYSIS:
- Knowledge Type: {knowledge_analysis.knowledge_type}
- Time Sensitivity: {knowledge_analysis.time_sensitivity}
- Requires Recent Info: {knowledge_analysis.requires_recent_information}

Determine:

1. **template**: The best format for this answer. Choose one:
   - "fact_card": Short factual answer (for simple lookups)
   - "deep_report": Comprehensive multi-section report (for research)
   - "tutorial": Step-by-step explanation (for how-to questions)
   - "shopping_comparison": Product comparison table (for shopping)
   - "match_summary": Sports score/match summary
   - "news_briefing": News summary with sources
   - "code_solution": Code with explanation
   - "comparison_table": Side-by-side comparison
   - "timeline": Chronological summary
   - "calculation": Math/logic result with steps

2. **depth**: How detailed should the answer be?
   - brief: 1-2 sentences
   - short: 1 paragraph
   - medium: 3-5 paragraphs
   - detailed: Full page
   - comprehensive: Multi-page report

3. **must_answer**: List of key aspects that MUST be addressed in the answer.

4. **optional**: Nice-to-have aspects.

5. **ignore**: Topics explicitly out of scope that should NOT be included.

Return strictly the structured output.
"""
        messages_to_send = [SystemMessage(content=system_prompt)]
        
        # Append the current query (coreferences already resolved by query_rewriter)
        user_query = state.get("user_query", "")
        messages_to_send.append(HumanMessage(content=user_query))
        # Build AnswerContract via LLM
        structured_llm = llm.with_structured_output(AnswerContract)
        backup_structured_llm = backup_model.with_structured_output(AnswerContract)

        answer_contract = await safe_llm_call(messages_to_send, structured_llm, backup_structured_llm)

        # Assemble the complete PlannerOutput
        planner_output = PlannerOutput(
            query_analysis=query_analysis,
            knowledge_analysis=knowledge_analysis,
            verification=verification,
            answer_contract=answer_contract
        )

        print(f"Answer Contract Builder took {time.time()-start:.2f}s")
        return {"planner_output": planner_output}
    except Exception as e:
        print(f"Answer Contract Builder failed after {time.time()-start:.2f}s: {e}")
        raise
