import asyncio
from agents.workflow import process_message_with_agents, stream_message_with_agents

async def test_static():
    print("=== Testing Static Query ===")
    query = "What is 2 + 2?"
    async for event in stream_message_with_agents(query, mode="complex"):
        print(event.strip())
        
async def test_dynamic():
    print("=== Testing Dynamic Query ===")
    query = "What is the weather in Tokyo right now?"
    async for event in stream_message_with_agents(query, mode="complex"):
        print(event.strip())

async def main():
    await test_static()
    print("\n\n")
    await test_dynamic()

if __name__ == "__main__":
    asyncio.run(main())
