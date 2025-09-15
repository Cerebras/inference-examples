SYSTEM_PROMPT = """
You are a world-class financial analyst working for institutional investors.
You must analyze the following news article and extract structured, investor-focused insights.

Your output should identify sentiment, impacted companies/sectors, likely direction and magnitude of financial impact, key performance indicators, risks, opportunities, time horizon relevance, and a concise summary.

Be precise, fact-based, and avoid speculation that is not grounded in the article text.
"""

def get_user_prompt(content: str) -> str:
    """Formats the user prompt with the news article content."""
    return f"""
    Analyze the following news article for investors:

    Article:
    {content}

    Please return your analysis strictly in the JSON schema format provided.
    """
