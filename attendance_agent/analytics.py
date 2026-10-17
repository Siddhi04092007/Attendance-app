import pandas as pd

def summarize_metrics(rows):
    if not rows:
        return {"samples": 0, "avg_faces": 0.0, "avg_recognized": 0.0,
                "avg_movement": 0.0, "audio_activity_samples": 0}
    df = pd.DataFrame(rows)
    return {
        "samples": int(len(df)),
        "avg_faces": round(float(df["faces_detected"].mean()), 2),
        "avg_recognized": round(float(df["recognized_count"].mean()), 2),
        "avg_movement": round(float(df["movement_score"].mean()), 4),
        "audio_activity_samples": int(df["audio_rms"].notna().sum()) if "audio_rms" in df else 0
    }

def local_suggestions(summary):
    suggestions = []
    if summary["samples"] == 0:
        return ["Run a session to collect aggregate metrics before generating suggestions."]
    if summary["avg_faces"] > 0 and summary["avg_recognized"] < summary["avg_faces"] * 0.5:
        suggestions.append("Review camera framing, lighting, and enrollment quality; many detected faces were not confidently recognized.")
    if summary["avg_movement"] < 0.002:
        suggestions.append("Consider a short question, poll, or pair discussion. Low movement is not proof of low attention.")
    if summary["audio_activity_samples"] == 0:
        suggestions.append("Audio activity was not sampled; enable optional microphone sampling only with consent.")
    suggestions.append("Use these signals as discussion prompts, not as a grade or definitive measure of engagement.")
    return suggestions
