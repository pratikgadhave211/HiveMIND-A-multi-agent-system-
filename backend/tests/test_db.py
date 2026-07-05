import asyncio
import sys
from psycopg_pool import AsyncConnectionPool

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def check():
    db_url = 'postgresql://postgres:password@localhost:5432/langgraph_db'
    try:
        async with AsyncConnectionPool(db_url, min_size=1, max_size=2) as pool:
            async with pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT count(*) FROM checkpoints")
                    row = await cur.fetchone()
                    print("Checkpoints count:", row[0])
    except Exception as e:
        print("Error:", e)

asyncio.run(check())
