import time
from agents.state import FINALSTATE, CriticOutput
from core.llm import llm, backup_model
from core.utils import safe_llm_call

async def critic_node(state: FINALSTATE):
    start = time.time()
    try:
        context = "\n\n".join(result.content for result in state["sources"])

        prompt = f"""
You are a research critic.
Question: {state['user_query']}
Research Findings: {context}

Determine:
1. Are there missing areas?
2. Are there weak arguments?
3. Are more searches needed?

Return structured output.
"""
        critic_model = llm.with_structured_output(CriticOutput)
        backup_critic_model = backup_model.with_structured_output(CriticOutput)
        critique = await safe_llm_call(prompt, critic_model, backup_critic_model)

        print(f"Critic took {time.time()-start:.2f}s")
        return {
            "critic_output": critique,
            "iteration_count": state["iteration_count"] + 1
         }
    except Exception as e:
        print(f"Critic failed after {time.time()-start:.2f}s")
        raise
