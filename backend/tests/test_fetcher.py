import asyncio
import sys

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def test():
    from agents.state import Source
    from agents.nodes.page_fetcher import page_fetcher_node

    print("Starting page fetcher test...")
    state = {
        "deduped_sources": [
            Source(title="Example", url="https://example.com", content="", source_type="test")
        ]
    }
    
    try:
        result = await asyncio.wait_for(page_fetcher_node(state), timeout=25.0)
        print("Page fetcher finished!", result)
    except Exception as e:
        print("Exception:", e)

asyncio.run(test())
