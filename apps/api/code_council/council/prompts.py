def build_analysis_prompt(code: str, language: str, mode: str) -> str:
    depth = "thorough" if mode == "thorough" else "concise"
    bug_limit = 6 if mode == "thorough" else 3
    suggestion_limit = 6 if mode == "thorough" else 3
    return f"""You are Code Council, an expert code reviewer.
Analyze the {language} code below and return valid JSON only.
Be {depth}. Do not include markdown fences or explanatory text outside JSON.

Return exactly this shape:
{{
  \"code_quality_score\": <number from 0 to 100>,
  \"potential_bugs\": [<up to {bug_limit} strings>],
  \"improvement_suggestions\": [<up to {suggestion_limit} strings>],
  \"documentation\": \"2-5 sentences explaining what the code does and the main risk areas\"
}}

Code:
{code}
"""


def build_multimodal_prompt(user_prompt: str | None = None) -> str:
    prompt = user_prompt.strip() if user_prompt else "Analyze this image and extract code or engineering-relevant details."
    return f"""{prompt}
Return a useful plain-text analysis that includes:
1. What the image shows
2. Any code that can be extracted
3. Bugs or risks you notice
4. Improvement suggestions
"""
