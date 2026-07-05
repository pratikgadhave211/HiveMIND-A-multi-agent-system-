import time
from agents.state import AssignmentState
from agents.tools import serper_search_tool

async def news_agent_node(state: AssignmentState):
    start = time.time()
    assignment = state.get("assignment")
    if not assignment:
        return {"sources": []}
    
    try:
        result_json = await serper_search_tool.ainvoke({"query": assignment.search_prompt, "search_type": "news"})
        from agents.state import SearchResult
        res = SearchResult.model_validate_json(result_json)
        sources = res.sources
    except Exception as e:
        print(f"News Agent Error: {e}")
        sources = []

    print(f"News Agent fetched {len(sources)} sources in {time.time()-start:.2f}s")
    return {"sources": sources}
