import time
from agents.state import FINALSTATE, KnowledgeAnalysis
from core.llm import llm, backup_model
from core.utils import safe_llm_call

async def knowledge_analyzer_node(state: FINALSTATE):
    """
    Step 2 of the semantic pipeline.
    Analyzes what TYPE of knowledge is being requested and its freshness requirements.
    This is purely descriptive — it never decides HOW to retrieve information.
    """
    start = time.time()
    try:
        structured_llm = llm.with_structured_output(KnowledgeAnalysis)
        backup_structured_llm = backup_model.with_structured_output(KnowledgeAnalysis)

        query_analysis = state.get("query_analysis_result")
        qa_context = ""
        if query_analysis:
            qa_context = f"""
Query Intent: {query_analysis.intent}
Domain: {query_analysis.domain}
Query Type: {query_analysis.query_type}
Complexity: {query_analysis.complexity}
"""

        prompt = f"""
You are a Knowledge Analyzer. Your job is to classify the TYPE of knowledge the user is requesting.
You must NEVER reference tools, APIs, search engines, or agents.
You only describe the knowledge characteristics.

USER QUERY: {state["user_query"]}

QUERY ANALYSIS:
{qa_context}

Determine:

1. **knowledge_type**: What category of knowledge is this?
   - static: Facts that rarely change (history, math, biographies, science concepts, programming syntax)
   - semi_dynamic: Information that changes periodically (product specs, university rankings, AI models, travel info)
   - dynamic: Information that changes frequently (news, politics, trends, stock market)
   - live: Information that changes in real-time (live scores, crypto prices, weather, flight status)

2. **time_sensitivity**: How time-sensitive is this information?
   - none: timeless (e.g., "Who was Napoleon?")
   - recent: within days/weeks (e.g., "Latest iPhone news")
   - today: within hours (e.g., "What happened in parliament today?")
   - live: right now (e.g., "Current Bitcoin price")

3. **expected_change_frequency**: How often does this information change?
   - never, yearly, monthly, weekly, daily, hourly, realtime

4. **freshness_window**: How recent must the information be? Use format like "24h", "7d", "30d", "30s", or null if freshness doesn't matter.

5. **volatility**: How unpredictable are changes to this information?
   - low: Python syntax, historical facts
   - medium: Product prices, university rankings
   - high: News, weather, stock market
   - extreme: Crypto prices, live scores, traffic

6. **requires_recent_information**: Does answering this query require fetching recent/current data? (true/false)

Return strictly the structured output.
"""
        result = await safe_llm_call(prompt, structured_llm, backup_structured_llm)
        print(f"Knowledge Analyzer took {time.time()-start:.2f}s")
        return {"knowledge_analysis_result": result}
    except Exception as e:
        print(f"Knowledge Analyzer failed after {time.time()-start:.2f}s: {e}")
        raise
