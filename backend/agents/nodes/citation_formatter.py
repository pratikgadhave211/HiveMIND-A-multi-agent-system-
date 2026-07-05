import time
from agents.state import FINALSTATE, FactCheckOutput, VerifiedClaim
from core.llm import llm, generate_model
from core.utils import safe_llm_call
from pydantic import BaseModel, Field
from typing import List

class CitationMapping(BaseModel):
    claim_index: int
    matched_urls: List[str]

class CitationFormatterOutput(BaseModel):
    mappings: List[CitationMapping]

async def citation_formatter_node(state: FINALSTATE):
    start = time.time()
    try:
        fact_check_output = state.get("fact_checker")
        if not fact_check_output or not fact_check_output.verified_claims:
            return {}

        claims = fact_check_output.verified_claims
        sources = state.get("sources", [])
        
        if not sources:
            return {}

        claims_text = "\n".join([f"{i}. {c.claim}" for i, c in enumerate(claims)])
        sources_text = "\n".join([f"[{s.url}]: {s.content[:300]}" for s in sources])

        prompt = f"""
You are the Citation Formatter. Match each claim to the most relevant source URLs.
Only link a source URL if the snippet truly supports the claim.

Claims:
{claims_text}

Available Sources:
{sources_text}

Return a list of mappings associating each claim_index with the matched_urls.
"""
        model = generate_model.with_structured_output(CitationFormatterOutput)
        response = await safe_llm_call(prompt, model, model)
        
        mappings = {m.claim_index: m.matched_urls for m in getattr(response, "mappings", [])}
        
        for i, claim in enumerate(claims):
            if i in mappings:
                claim.citations = mappings[i]
                
        print(f"Citation Formatter took {time.time()-start:.2f}s")
        return {"fact_checker": FactCheckOutput(verified_claims=claims)}
    except Exception as e:
        print(f"Citation Formatter failed after {time.time()-start:.2f}s: {str(e)}")
        # Fail gracefully, return state as is
        return {}
