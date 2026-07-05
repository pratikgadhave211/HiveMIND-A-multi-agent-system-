import asyncio
import sys

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from agents.workflow import graph

async def test():
    config = {"configurable": {"thread_id": "test_hang_123"}}
    inputs = {
        "user_query": "what was the question",
        "messages": [("user", "what was the question")],
        "iteration_count": 0,
        "search_mode": "complex"
    }
    
    print("Starting graph...")
    async for event in graph.astream_events(inputs, config=config, version="v2"):
        kind = event.get("event", "")
        node = event.get("name", "")
        if kind == "on_chain_start":
            print(f"Started {node}")
        elif kind == "on_chain_end":
            print(f"Finished {node}")

asyncio.run(test())
