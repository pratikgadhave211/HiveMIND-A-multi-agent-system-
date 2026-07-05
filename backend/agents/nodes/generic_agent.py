import time
import asyncio
from agents.state import AssignmentState
from agents.tools import serper_search_tool

async def generic_agent_node(state: AssignmentState):
    start = time.time()
    assignment = state.get("assignment")
    if not assignment:
        return {"sources": []}
    
    try:
        # Strictly use googlesearch (via Serper API) to fetch the latest URLs
        result_json = await serper_search_tool.ainvoke({"query": assignment.search_prompt})
        from agents.state import SearchResult
        res = SearchResult.model_validate_json(result_json)
        # Keep only the latest 2-3 URLs (we will restrict to 3)
        sources = res.sources[:3]
    except Exception as e:
        print(f"Generic Agent Error: {e}")
        sources = []

    print(f"Generic Agent fetched {len(sources)} sources from Google in {time.time()-start:.2f}s")
    return {"sources": sources}

# Aliases for other agents so workflow.py doesn't break
live_score_agent_node = generic_agent_node
finance_agent_node = generic_agent_node
coding_agent_node = generic_agent_node
