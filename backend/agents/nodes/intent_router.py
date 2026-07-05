import time
from agents.state import FINALSTATE, IntentOutput

async def intent_router_node(state: FINALSTATE):
    start = time.time()
    
    # Read the search_mode from the state (passed directly from the UI toggle)
    # Default to "simple" (Fast Search) if missing
    intent = state.get("search_mode", "simple")

    elapsed = time.time() - start
    print(f"Intent Router (manual) took {elapsed:.2f}s -> {intent}")
    return {
        "intent_output": IntentOutput(intent=intent),
        "sources": "CLEAR",
        "chunks": "CLEAR",
        "deduped_sources": [],
        "reranked_chunks": [],
        "fetched_content": "",
        "synthesized_context": "",
        "fact_checker": None,
        "critic_output": None,
        "iteration_count": 0
    }
