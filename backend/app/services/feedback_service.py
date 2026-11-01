"""Final feedback generation. Thin wrapper that assembles interview context and
delegates to Gemini (with a graceful fallback inside gemini_service)."""
from __future__ import annotations

from typing import Dict, List

from app.services import gemini_service


def build_transcript(qa_pairs: List[Dict]) -> str:
    """Turn Q/A/eval tuples into a compact transcript for the feedback prompt."""
    lines: List[str] = []
    for i, qa in enumerate(qa_pairs, start=1):
        lines.append(f"Q{i}: {qa.get('question', '')}")
        lines.append(f"A{i}: {qa.get('transcript', '') or '(no answer)'}")
        ev = qa.get("evaluation")
        if ev:
            lines.append(
                f"Scores -> answer_quality: {ev.get('answer_quality_score')}, "
                f"communication: {ev.get('communication_score')}"
            )
        lines.append("")
    return "\n".join(lines)


def generate_final_feedback(
    category: str,
    difficulty: str,
    overall_score: float,
    aggregate: Dict[str, float],
    qa_pairs: List[Dict],
) -> Dict:
    """Produce the final personalized feedback report."""
    transcript = build_transcript(qa_pairs)
    feedback = gemini_service.generate_feedback(
        category=category,
        difficulty=difficulty,
        overall_score=overall_score,
        aggregate=aggregate,
        transcript=transcript,
    )
    feedback["overall_score"] = round(overall_score, 1)
    return feedback
