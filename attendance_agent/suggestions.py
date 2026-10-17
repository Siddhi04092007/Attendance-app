from .config import ENABLE_CLOUD_AI, GEMINI_API_KEY, GEMINI_MODEL

def teaching_suggestions(summary):
    """Cloud mode sends aggregate counts only; local fallback always works."""
    if ENABLE_CLOUD_AI and GEMINI_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=GEMINI_API_KEY)
            prompt = (
                "You are an educator-support assistant. Give 3 concise, low-stakes teaching ideas "
                "based only on these anonymous aggregate classroom activity metrics. Do not infer "
                "individual student attention, emotion, ability, or intent. State that proxies are uncertain. "
                f"Metrics: {summary}"
            )
            response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
            if response.text:
                return {"source": "Optional cloud AI (aggregate metrics only)",
                        "suggestions": [line.strip("- •\\n ") for line in response.text.splitlines() if line.strip()]}
        except Exception as exc:
            return {"source": "Local fallback (cloud request failed)",
                    "suggestions": [f"Cloud AI unavailable: {type(exc).__name__}.",
                                    "Try a brief poll or think-pair-share, then review participation qualitatively."]}
    from .analytics import local_suggestions
    return {"source": "Local rule-based suggestions", "suggestions": local_suggestions(summary)}
