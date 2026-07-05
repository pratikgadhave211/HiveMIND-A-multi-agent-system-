import time
from agents.state import FINALSTATE, OrchestratorOutput, Assignment
from core.llm import llm, backup_model
from core.utils import safe_llm_call

# Capability -> Agent mapping (implementation detail, stays here)
CAPABILITY_TO_AGENT = {
    "general_search": "general_agent",
    "news": "news_agent",
    "live_score": "live_score_agent",
    "finance": "finance_agent",
    "shopping": "shopping_agent",
    "coding": "coding_agent",
}

async def orchestrator(state: FINALSTATE):
    """
    The Orchestrator. Reads the ExecutionStrategy and decomposes the query
    into concrete search assignments, routing each to the appropriate agent
    based on capability mapping.
    """
    start = time.time()
    try:
        execution_strategy = state["execution_strategy"]
        planner_output = state["planner_output"]

        # If no retrieval needed, return empty assignments immediately
        if not execution_strategy.needs_retrieval:
            print(f"Orchestrator took {time.time()-start:.2f}s -> No retrieval needed, skipping agents.")
            return {"decompose_tasks": OrchestratorOutput(
                research_goal=planner_output.query_analysis.intent,
                assignments=[]
            )}

        structured_llm = llm.with_structured_output(OrchestratorOutput)
        backup_structured_llm = backup_model.with_structured_output(OrchestratorOutput)

        capabilities_str = ", ".join(execution_strategy.required_capabilities)

        prompt = f"""
You are the Orchestrator. The user asked: "{state['user_query']}"

Your job is to decompose this query into specific search assignments.

EXECUTION STRATEGY:
- Mode: {execution_strategy.execution_mode}
- Required Capabilities: {capabilities_str}
- Max Sources: {execution_strategy.max_sources}
- Reasoning Strategy: {execution_strategy.reasoning_strategy}

SEMANTIC ANALYSIS:
- Intent: {planner_output.query_analysis.intent}
- Domain: {planner_output.query_analysis.domain}
- Complexity: {planner_output.query_analysis.complexity}
- Must Answer: {planner_output.answer_contract.must_answer}
- Ignore: {planner_output.answer_contract.ignore}

CRITICAL INSTRUCTIONS:
1. Every assignment must directly help answer the user's question.
2. Each assignment needs: question, priority, capability, search_prompt, needs_deep_search.
3. The "capability" field must be one of: {capabilities_str}
4. Create max {min(planner_output.query_analysis.estimated_tasks, 3)} assignments.
5. NEVER generate an assignment that covers anything in the ignore list: {planner_output.answer_contract.ignore}
6. SUFFICIENCY CHECK: If iteration_count > 0 and existing sources are sufficient, return empty assignments.

Return only valid structured output.
"""
        result = await safe_llm_call(prompt, structured_llm, backup_structured_llm)
        print(f"Orchestrator took {time.time()-start:.2f}s -> {len(result.assignments)} assignments")
        return {"decompose_tasks": result}
    except Exception as e:
        print(f"Orchestrator failed after {time.time()-start:.2f}s: {e}")
        raise
