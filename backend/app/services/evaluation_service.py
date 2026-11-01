"""Performance Evaluation Engine.

Gemini evaluates the semantic and technical quality of the answer, while the
speech and computer-vision modules provide communication and non-verbal
metrics. This engine COMBINES those metrics using a configurable weighted
scoring mechanism. There is no separate trained ML model here.
"""
from __future__ import annotations

from typing import Dict, Optional

from app.core.config import settings


def compute_answer_quality(quality: Dict) -> float:
    """Convert Gemini's 0-10 sub-scores into a single 0-100 answer-quality score.

    Weights within answer quality:
      technical 35%, relevance 30%, completeness 20%, clarity 15%.
    """
    technical = float(quality.get("technical_score", 0))
    relevance = float(quality.get("relevance_score", 0))
    completeness = float(quality.get("completeness_score", 0))
    clarity = float(quality.get("clarity_score", 0))

    blended_0_10 = (
        technical * 0.35
        + relevance * 0.30
        + completeness * 0.20
        + clarity * 0.15
    )
    return round(max(0.0, min(100.0, blended_0_10 * 10.0)), 1)


def combine_scores(
    quality: Dict,
    speech_metrics: Optional[Dict],
    vision_metrics: Optional[Dict],
) -> Dict:
    """Combine answer-quality, communication and non-verbal metrics.

    Returns a dict of normalised (0-100) component scores plus the overall score.
    If vision is unavailable, its weight is redistributed to the remaining
    components so the candidate is not unfairly penalised.
    """
    weights = dict(settings.evaluation_weights)

    answer_quality = compute_answer_quality(quality)
    communication = float((speech_metrics or {}).get("communication_score", 0.0))

    vision_available = bool(vision_metrics and vision_metrics.get("available"))
    if vision_available:
        eye_contact = float(vision_metrics.get("eye_contact_percentage", 0.0))
        posture = float(vision_metrics.get("posture_score", 0.0))
        gesture = float(vision_metrics.get("gesture_score", 0.0))
    else:
        eye_contact = posture = gesture = 0.0

    if not vision_available:
        # Redistribute vision weight across answer quality + communication.
        vision_weight = (
            weights["eye_contact"] + weights["posture"] + weights["gesture"]
        )
        total_kept = weights["answer_quality"] + weights["communication"]
        if total_kept > 0:
            weights["answer_quality"] += vision_weight * (
                weights["answer_quality"] / total_kept
            )
            weights["communication"] += vision_weight * (
                weights["communication"] / total_kept
            )
        weights["eye_contact"] = weights["posture"] = weights["gesture"] = 0.0

    overall = (
        answer_quality * weights["answer_quality"]
        + communication * weights["communication"]
        + eye_contact * weights["eye_contact"]
        + posture * weights["posture"]
        + gesture * weights["gesture"]
    )

    return {
        "technical_score": round(float(quality.get("technical_score", 0)), 1),
        "relevance_score": round(float(quality.get("relevance_score", 0)), 1),
        "completeness_score": round(float(quality.get("completeness_score", 0)), 1),
        "clarity_score": round(float(quality.get("clarity_score", 0)), 1),
        "answer_quality_score": answer_quality,
        "communication_score": round(communication, 1),
        "eye_contact_score": round(eye_contact, 1),
        "posture_score": round(posture, 1),
        "gesture_score": round(gesture, 1),
        "overall_score": round(max(0.0, min(100.0, overall)), 1),
        "remarks": quality.get("remarks", ""),
    }


def aggregate_interview(evaluations: list) -> Dict:
    """Average the per-answer component scores across the whole interview."""
    if not evaluations:
        return {
            "answer_quality": 0.0,
            "communication": 0.0,
            "eye_contact": 0.0,
            "posture": 0.0,
            "gesture": 0.0,
            "overall": 0.0,
        }

    def avg(attr: str) -> float:
        vals = [getattr(e, attr, 0.0) or 0.0 for e in evaluations]
        return round(sum(vals) / len(vals), 1) if vals else 0.0

    return {
        "answer_quality": avg("answer_quality_score"),
        "communication": avg("communication_score"),
        "eye_contact": avg("eye_contact_score"),
        "posture": avg("posture_score"),
        "gesture": avg("gesture_score"),
        "overall": avg("overall_score"),
    }
