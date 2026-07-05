import time
from agents.state import FINALSTATE, ExecutionStrategy
from agents.rag import has_documents

async def execution_planner_node(state: FINALSTATE):
    """
    The Execution Planner. Bridges the semantic world to the execution world.
    Reads the PlannerOutput (semantic) and decides HOW to solve the problem.
    This is a deterministic rules-based engine — no LLM needed.
    """
    start = time.time()
    try:


        planner_output = state["planner_output"]
        ka = planner_output.knowledge_analysis
        qa = planner_output.query_analysis

        # --- Determine execution_mode ---
        if ka.knowledge_type == "static" and not ka.requires_recent_information:
            execution_mode = "internal_reasoning"
            needs_retrieval = False
        elif ka.knowledge_type == "live":
            execution_mode = "live_data"
            needs_retrieval = True
        elif ka.knowledge_type in ("dynamic", "semi_dynamic") or ka.requires_recent_information:
            execution_mode = "web_search"
            needs_retrieval = True
        else:
            execution_mode = "internal_reasoning"
            needs_retrieval = False
            
        # Force retrieval if a local document is uploaded
        if has_documents():
            needs_retrieval = True

        # --- Determine required_capabilities ---
        required_capabilities = []
        if needs_retrieval:
            qt = qa.query_type
            if qt == "live_score":
                required_capabilities.append("live_score")
            elif qt == "news":
                required_capabilities.append("news")
            elif qt == "shopping":
                required_capabilities.append("shopping")
            elif qt == "coding":
                required_capabilities.append("coding")
            elif qa.domain == "finance":
                required_capabilities.append("finance")
            else:
                required_capabilities.append("general_search")

        # --- Determine max_sources ---
        if qa.complexity == "simple":
            max_sources = 3
        elif qa.complexity == "medium":
            max_sources = 5
        else:
            max_sources = 10

        strategy = ExecutionStrategy(
            execution_mode=execution_mode,
            needs_retrieval=needs_retrieval,
            required_capabilities=required_capabilities,
            reasoning_strategy=qa.reasoning_strategy,
            max_sources=max_sources,
        )

        print(f"Execution Planner took {time.time()-start:.2f}s -> mode={execution_mode}, retrieval={needs_retrieval}, caps={required_capabilities}")
        return {"execution_strategy": strategy}
    except Exception as e:
        print(f"Execution Planner failed after {time.time()-start:.2f}s: {e}")
        raise
