import asyncio
import re

def _is_rate_limit_error(error: Exception) -> bool:
    """Check if error is a rate limit (429, 413, or TPM exceeded)"""
    error_str = str(error).lower()
    return any(x in error_str for x in ["rate_limit", "429", "413", "tpm:", "too large"])

def _is_retryable_error(error: Exception) -> bool:
    """Check if error is worth retrying vs permanent failure"""
    error_str = str(error).lower()
    if any(x in error_str for x in ["failed to parse", "invalid_request", "tool_use_failed", "invalid json"]):
        return False
    if any(x in error_str for x in ["rate_limit", "429", "500", "503", "timeout", "connection"]):
        return True
    return False

def _compress_prompt(prompt, target_ratio: float = 0.8):
    """Compress prompt by removing examples and reducing context"""
    if isinstance(prompt, list):
        return prompt  # Do not compress if it's a list of messages for now
    compressed = re.sub(r'(?i)(EXAMPLE|EXAMPLES):\s*\{[\s\S]*?\n}', '', prompt)
    compressed = re.sub(r'(?i)(--+)\s*\n[\s\S]{0,500}?\n(--+)', '', compressed)
    compressed = re.sub(r'\n{3,}', '\n\n', compressed)
    return compressed

async def safe_llm_call(
    prompt,
    primary_model,
    backup_model,
    max_retries: int = 6,
    enable_compression: bool = True
):
    """
    Intelligent retry wrapper with exponential backoff.
    Falls back to backup_model if primary exhausts retries.
    """
    last_error = None

    for attempt in range(max_retries):
        try:
            result = await primary_model.ainvoke(prompt)
            if result is None:
                raise ValueError("Model returned None. Likely failed to parse structured output.")
            return result
        except Exception as e:
            last_error = e
            is_rate_limit = _is_rate_limit_error(e)
            is_retryable = _is_retryable_error(e)

            error_type = "rate_limit" if is_rate_limit else ("transient" if is_retryable else "permanent")
            print(f"Primary attempt {attempt + 1} failed ({error_type}): {str(e)[:120]}")

            if not is_retryable:
                print("Permanent error, switching to backup.")
                break

            if attempt < max_retries - 1:
                wait_time = 3 ** (attempt + 1)
                if is_rate_limit and enable_compression and attempt == 1:
                    prompt = _compress_prompt(prompt)
                print(f"Waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)

    # Try backup model
    print("Primary exhausted. Trying backup model...")
    try:
        result = await backup_model.ainvoke(prompt)
        if result is None:
            raise ValueError("Backup model returned None.")
        return result
    except Exception as e:
        print(f"Backup model also failed: {str(e)[:120]}")
        raise Exception(f"All models failed. Last primary error: {last_error}") from e
