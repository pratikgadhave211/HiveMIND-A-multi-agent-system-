import time
import asyncio
from agents.state import FINALSTATE
from agents.tools import jina_fetch_tool

async def page_fetcher_node(state: FINALSTATE):
    start = time.time()
    semaphore = asyncio.Semaphore(10)
    sources_to_fetch = state.get("deduped_sources", state.get("sources", []))
    
    fetched_sources = []
    
    async def fetch_source(source):
        async with semaphore:
            if not source.url:
                return source
            try:
                result_json = await jina_fetch_tool.ainvoke({"url": source.url})
                from agents.state import SearchResult
                res = SearchResult.model_validate_json(result_json)
                if res.sources and res.sources[0].content:
                    source.content = res.sources[0].content # Update snippet with full content
            except Exception as e:
                pass
            return source

    fetched_sources = await asyncio.gather(*(fetch_source(s) for s in sources_to_fetch))
    print(f"Page Fetcher fetched {len(fetched_sources)} pages in {time.time()-start:.2f}s")
    
    combined_content = "\n\n".join([f"Source: {s.url}\n\n{s.content}" for s in fetched_sources if s.content])
    return {"deduped_sources": fetched_sources, "fetched_content": combined_content}
