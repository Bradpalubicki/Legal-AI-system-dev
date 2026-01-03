
from src.core.foundation_repair import AdviceNeutralizer

neutralizer = AdviceNeutralizer()

def neutralize_ai_output(text: str) -> str:
    """Neutralize advice language in AI output"""
    result = neutralizer.scan_and_neutralize(text)

    if result['requires_human_review']:
        # Log for human review
        pass

    return result['neutralized_text']

def advice_neutralization_middleware(func):
    """Middleware to neutralize advice in function outputs"""
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)

        if isinstance(result, str):
            return neutralize_ai_output(result)
        elif isinstance(result, dict) and 'content' in result:
            result['content'] = neutralize_ai_output(result['content'])
            return result

        return result

    return wrapper
