import time
from langchain_text_splitters import MarkdownTextSplitter
from agents.state import FINALSTATE, Chunk

async def chunking_engine_node(state: FINALSTATE):
    start = time.time()
    sources = state.get("deduped_sources", [])
    
    splitter = MarkdownTextSplitter(chunk_size=1000, chunk_overlap=100)
    all_chunks = []
    
    for source in sources:
        if not source.content:
            continue
        texts = splitter.split_text(source.content)
        for text in texts:
            all_chunks.append(Chunk(content=text, source_url=source.url))
            
    print(f"Chunking Engine created {len(all_chunks)} chunks in {time.time()-start:.2f}s")
    return {"chunks": all_chunks}
