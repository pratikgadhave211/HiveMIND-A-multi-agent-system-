import asyncio
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

async def main():
    serde = JsonPlusSerializer(allowed_msgpack_modules=[
        ('agents.state', 'PlannerOutput')
    ])
    try:
        # We just want to see if this throws an error or not
        cp = AsyncPostgresSaver(None, serde=serde)
        print("Success")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(main())
