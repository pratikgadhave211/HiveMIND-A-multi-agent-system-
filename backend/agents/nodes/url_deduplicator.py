import time
from agents.state import FINALSTATE

async def url_deduplicator_node(state: FINALSTATE):
    start = time.time()
    seen = set()
    unique_sources = []
    
    for source in state["sources"]:
        if source.url and source.url not in seen:
            seen.add(source.url)
            unique_sources.append(source)
        elif not source.url:
            unique_sources.append(source)
            
    print(f"URL Deduplicator removed {len(state['sources']) - len(unique_sources)} duplicates in {time.time()-start:.2f}s")
    return {"deduped_sources": unique_sources}
