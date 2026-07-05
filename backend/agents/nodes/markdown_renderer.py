import time
from agents.state import FINALSTATE

async def markdown_renderer_node(state: FINALSTATE):
    """
    Markdown Renderer. Converts the StructuredResponse into a final Markdown string.
    This is a pure presentation layer — no LLM needed.
    """
    start = time.time()
    try:
        structured_response = state["structured_response"]

        parts = []

        # Title
        if structured_response.title:
            parts.append(f"# {structured_response.title}")
            parts.append("")

        # Summary
        if structured_response.summary:
            parts.append(f"_{structured_response.summary}_")
            parts.append("")

        # Sections
        for section in structured_response.sections:
            parts.append(f"## {section.heading}")
            parts.append("")
            parts.append(section.content)
            parts.append("")

        # Confidence
        if structured_response.confidence_score is not None:
            parts.append("---")
            parts.append(f"**Confidence Score:** {structured_response.confidence_score:.1f}%")
            parts.append("")

        final_markdown = "\n".join(parts)

        print(f"Markdown Renderer took {time.time()-start:.2f}s ({len(final_markdown)} chars)")
        return {"final_report": final_markdown}
    except Exception as e:
        print(f"Markdown Renderer failed after {time.time()-start:.2f}s: {e}")
        raise
