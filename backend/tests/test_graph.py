import asyncio
from agents.workflow import graph

async def main():
    print("Graph compiled successfully!")
    print("Nodes:", graph.nodes.keys())

asyncio.run(main())
