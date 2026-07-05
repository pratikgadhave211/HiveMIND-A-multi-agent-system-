import asyncio
from agents.nodes.orchestrator import orchestrator
from agents.state import ResearchPlan

async def run():
    plan = ResearchPlan(
        query_type='research', 
        research_subjects=['AI'], 
        dimensions=['future'], 
        source_types=['tavily']
    )
    state = {
        'user_query': 'Impact of autonomous AI on software engineering', 
        'planner': plan,
        'iteration_count': 0
    }
    res = await orchestrator(state)
    print(res)

if __name__ == "__main__":
    asyncio.run(run())
