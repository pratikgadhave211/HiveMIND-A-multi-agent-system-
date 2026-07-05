import time
from agents.state import FINALSTATE, QueryAnalysis, KnowledgeAnalysis, VerificationStrategy, AnswerContract, PlannerOutput
from core.llm import llm, backup_model
from core.utils import safe_llm_call

from langchain_core.messages import SystemMessage, HumanMessage

async def query_analyzer_node(state: FINALSTATE):
    """
    Step 1 of the semantic pipeline.
    Understands the user's intent, domain, complexity, and reasoning strategy.
    Produces a purely semantic analysis — no awareness of agents, tools, or APIs.
    """
    start = time.time()
    try:
        structured_llm = llm.with_structured_output(QueryAnalysis)
        backup_structured_llm = backup_model.with_structured_output(QueryAnalysis)

        system_prompt = """
You are a Query Analyzer. Your job is to deeply understand what the user is asking.
You must NEVER reference specific tools, APIs, search engines, or agent names.
You only describe the semantic properties of the query.

Analyze the query and determine:

1. **intent**: What is the user trying to do?
   - information_request: wants to know something
   - comparison: wants to compare things
   - recommendation: wants suggestions
   - calculation: wants a math/logic answer
   - explanation: wants something explained
   - live_data: wants real-time information
   - creative: wants creative content
   - conversational: casual chat / follow-up
   - action_request: wants something done

2. **domain**: The topic area (e.g., "sports", "finance", "programming", "science", "people", "general")

3. **query_type**: More specific classification:
   - fact_lookup: simple factual question
   - deep_research: needs multi-source research
   - live_score: live sports data
   - news: current events
   - shopping: product search
   - coding: programming help
   - opinion: subjective question
   - tutorial: how-to / explanation
   - comparison: comparing options
   - calculation: math/logic
   - general: doesn't fit above

4. **complexity**: simple (1 search), medium (2-3 sub-tasks), high (4+ sub-tasks)

5. **estimated_tasks**: Number of sub-tasks needed (1-10)

6. **parallelizable**: Can sub-tasks run in parallel?

7. **reasoning_strategy**: What reasoning approach is needed?
   - none: direct answer, no reasoning
   - summarize: condense information
   - compare: side-by-side evaluation
   - timeline: chronological ordering
   - calculate: mathematical reasoning
   - explain: pedagogical explanation
   - verify: fact-checking
   - synthesize: combine multiple perspectives
   - decompose: break into sub-problems
   - multi_hop: chain of reasoning steps

Return strictly the structured output.
"""
        messages_to_send = [SystemMessage(content=system_prompt)]
        
        # Append the entire chat history (which includes the current query at the end)
        messages = state.get("messages", [])
        messages_to_send.extend(messages)

        result = await safe_llm_call(messages_to_send, structured_llm, backup_structured_llm)
        print(f"Query Analyzer took {time.time()-start:.2f}s")
        return {"query_analysis_result": result}
    except Exception as e:
        print(f"Query Analyzer failed after {time.time()-start:.2f}s: {e}")
        raise
