import time
import asyncio
from agents.state import FINALSTATE, FactCheckOutput
from core.llm import llm
from core.utils import safe_llm_call

async def verify_chunk(chunk, user_query):
    sources_text = "\n".join(f"[{s.url}]: {s.content}" for s in chunk)
    prompt = f"""
Verify the following findings.
Question: {user_query}
Findings: 
{sources_text}

For each important claim:
1. Verify if supported by the findings.
2. Evaluate 5 trust dimensions (each 0-100):
   - source_count_score: How many independent sources?
   - source_authority_score: High for academic/gov, medium for news, low for random blogs.
   - source_agreement_score: Do the sources agree?
   - recency_score: Is the information recent?
   - fact_checker_verdict_score: Overall confidence in verification.
3. Calculate final trust_score (0-100) as the average of the 5 dimensions.
4. Provide the extracted claim, the final trust score, the detailed dimensions, and your reasoning (evidence).

Return strictly adhering to the schema.
"""
    factcheck_model = llm.with_structured_output(FactCheckOutput)
    return await safe_llm_call(prompt, factcheck_model, factcheck_model)

def chunk_sources(sources, chunk_size=10):
    return [sources[i:i+chunk_size] for i in range(0, len(sources), chunk_size)]

async def fact_checker_node(state: FINALSTATE):
    start = time.time()
    semaphore = asyncio.Semaphore(2)
    async def verify_chunk_with_sem(chunk, user_query):
        async with semaphore:
            return await verify_chunk(chunk, user_query)
    try:
        chunks = chunk_sources(state["sources"], chunk_size=15)
        all_claims = []
        tasks = [verify_chunk_with_sem(chunk, state["user_query"]) for chunk in chunks]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                continue
            if result and hasattr(result, "verified_claims"):
                if result.verified_claims:
                    all_claims.extend(result.verified_claims)

        print(f"Fact Checker took {time.time()-start:.2f}s")
        return {"fact_checker": FactCheckOutput(verified_claims=all_claims)}
    except Exception as e:
        print(f"Fact Checker failed after {time.time()-start:.2f}s")
        raise
