"""
Centralized AI Prompt Configuration - CONCISE ONLY
NO VERBOSE PROMPTS - NO HARVARD PROFESSOR MODE
"""

# ONLY CONCISE PROMPTS FOR MAXIMUM SPEED
AI_PROMPTS = {
    # DEFAULT ULTRA-CONCISE PROMPT
    "default": {
        "system": "Answer in max 3 sentences. No metaphors. Be direct.",
        "template": lambda query: f"Question: {query}\nAnswer:",
        "model": "claude-3-5-haiku-20241022",
        "max_tokens": 500,
        "temperature": 0
    },

    # Q&A SYSTEM - ULTRA FAST
    "qa": {
        "system": "Legal answer in 2 sentences max. Simple words only.",
        "template": lambda query: f"Legal question: {query}\nDirect answer:",
        "model": "claude-3-5-haiku-20241022",
        "max_tokens": 200,
        "temperature": 0
    },

    # DOCUMENT ANALYSIS - CONCISE
    "document_analysis": {
        "system": "Summarize in 3 bullet points only.",
        "template": lambda doc: f"Document: {doc[:1000]}\nKey points:",
        "model": "claude-3-5-haiku-20241022",
        "max_tokens": 300,
        "temperature": 0
    },

    # DEFENSE BUILDER - DIRECT
    "defense_builder": {
        "system": "List 3 defense options with requirements.",
        "template": lambda case: f"Case: {case}\nDefenses:",
        "model": "claude-3-5-haiku-20241022",
        "max_tokens": 400,
        "temperature": 0
    },

    # STRATEGIC QUESTIONS - FAST
    "strategic": {
        "system": "Generate 3 specific questions only.",
        "template": lambda context: f"Context: {context}\nQuestions:",
        "model": "claude-3-5-haiku-20241022",
        "max_tokens": 200,
        "temperature": 0
    }
}

# ULTRA-CONCISE BASE PROMPT - FASTEST SPEED
ULTRA_CONCISE_PROMPT = """Rules:
- Maximum 3 sentences
- Simple words only
- No metaphors or stories
- Start with the answer
- Use bullet points for lists

Question: {query}
Answer:"""

# DEFENSE-FOCUSED PROMPT - LEGAL SPECIFIC
DEFENSE_PROMPT = """Defense options: [list 3]. Evidence needed: [list]. Answer in 3 sentences max.

Question: {query}
Answer:"""

def get_prompt(prompt_type: str = "default") -> dict:
    """Get concise prompt configuration by type"""
    return AI_PROMPTS.get(prompt_type, AI_PROMPTS["default"])

def format_prompt(prompt_type: str, content: str) -> str:
    """Format content with specified prompt type"""
    config = get_prompt(prompt_type)
    return config["template"](content)

def get_model_config(prompt_type: str = "default") -> dict:
    """Get model configuration for prompt type"""
    config = get_prompt(prompt_type)
    return {
        "model": config["model"],
        "max_tokens": config["max_tokens"],
        "temperature": config["temperature"]
    }

# REMOVE ALL VERBOSE PROMPTS BELOW THIS LINE
# NO HARVARD PROFESSOR MODE
# NO DETAILED EXPLANATIONS
# NO LONG SYSTEM MESSAGES