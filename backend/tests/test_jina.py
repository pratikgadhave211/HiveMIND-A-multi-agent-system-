import asyncio
from agents.tools import jina_fetch_tool

async def run():
    print("Testing Jina...")
    # A random URL
    res = await jina_fetch_tool.ainvoke({"url": "https://en.wikipedia.org/wiki/Artificial_intelligence"})
    print("Length of result:", len(res))

if __name__ == "__main__":
    asyncio.run(run())
