"""Google Gemini integration for the AI interviewer.

This service is responsible for:
  - generate_question()          -> the very first interview question
  - generate_follow_up_question()-> dynamic follow-up / next question
  - evaluate_answer()            -> answer-quality scoring (0-10 sub-scores)
  - generate_feedback()          -> final personalized interview report

Every call is defensive: if the Gemini API key is missing, the network fails,
rate limits are hit, or the model returns malformed JSON, we degrade gracefully
instead of crashing the interview.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

from app.core.config import settings

logger = logging.getLogger("gemini_service")

# The google-genai client is created lazily so the app can boot without a key.
_client = None
_client_init_failed = False


def _get_client():
    global _client, _client_init_failed
    if _client is not None:
        return _client
    if _client_init_failed:
        return None
    if not settings.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY is not set; using offline fallbacks.")
        _client_init_failed = True
        return None
    try:
        from google import genai  # imported lazily

        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return _client
    except Exception as exc:  # pragma: no cover - depends on environment
        logger.error("Failed to initialise Gemini client: %s", exc)
        _client_init_failed = True
        return None


def _call_gemini(prompt: str) -> Optional[str]:
    """Send a prompt to Gemini and return the raw text, or None on any failure."""
    client = _get_client()
    if client is None:
        return None
    try:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
        )
        return (response.text or "").strip()
    except Exception as exc:  # rate limits, network, quota, etc.
        logger.error("Gemini API call failed: %s", exc)
        return None


def _extract_json(text: str) -> Optional[dict]:
    """Robustly pull a JSON object out of an LLM response.

    Handles: raw JSON, ```json fenced blocks, and JSON embedded in prose.
    """
    if not text:
        return None

    # 1) Strip common markdown fences.
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()

    # 2) Try a direct parse.
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # 3) Find the first balanced {...} block.
    start = cleaned.find("{")
    while start != -1:
        depth = 0
        for i in range(start, len(cleaned)):
            if cleaned[i] == "{":
                depth += 1
            elif cleaned[i] == "}":
                depth -= 1
                if depth == 0:
                    candidate = cleaned[start : i + 1]
                    try:
                        return json.loads(candidate)
                    except Exception:
                        break
        start = cleaned.find("{", start + 1)
    return None


def _resume_to_text(resume: Optional[Dict[str, Any]]) -> str:
    """Compact a structured resume dict into a prompt-friendly string."""
    if not resume:
        return "No resume provided."
    parts: List[str] = []
    if resume.get("name"):
        parts.append(f"Name: {resume['name']}")
    if resume.get("summary"):
        parts.append(f"Summary: {resume['summary']}")
    for key in [
        "education",
        "skills",
        "programming_languages",
        "frameworks",
        "technologies",
        "projects",
        "internships",
        "certifications",
        "experience",
    ]:
        val = resume.get(key)
        if val:
            if isinstance(val, list):
                val = ", ".join(str(v) for v in val)
            parts.append(f"{key.replace('_', ' ').title()}: {val}")
    return "\n".join(parts) if parts else "No structured resume data."


# ----------------------------------------------------------------------------
# Question generation
# ----------------------------------------------------------------------------
QUESTION_PROMPT = """You are an experienced technical interviewer conducting a realistic, professional job interview.

Candidate Resume:
{resume}

Interview Category: {category}
Difficulty: {difficulty}

Previous Questions:
{previous_questions}

Previous Answers:
{previous_answers}

Current Interview Context:
{context}

Generate exactly ONE interview question.

The question MUST:
- Match the selected category ({category}).
- Match the selected difficulty ({difficulty}).
- Be relevant to the candidate's resume where possible.
- Avoid repeating any previous question.
- If a previous answer opens the door to deeper questioning, ask a natural follow-up.
- Sound like a real human interviewer speaking to the candidate.
- Be a single question (do NOT ask multiple questions at once).
- Do NOT provide or hint at the answer.

Difficulty guidance:
- Easy: fundamentals, basic resume clarification, simple concepts.
- Medium: intermediate concepts, project-based and practical scenario questions.
- Hard: advanced concepts, system/design thinking, deep problem solving.

Return ONLY valid JSON in this exact shape:
{{
  "question": "the question text",
  "category": "{category}",
  "difficulty": "{difficulty}",
  "question_type": "{qtype}"
}}"""


FOLLOWUP_PROMPT = """You are an experienced technical interviewer in the MIDDLE of a live, realistic interview. You have already asked earlier questions and the candidate has answered. Now ask the NEXT question, speaking naturally like a real human interviewer.

Candidate Resume:
{resume}

Interview Category: {category}
Difficulty: {difficulty}

Questions you have ALREADY asked (NEVER repeat or lightly rephrase any of these):
{previous_questions}

The candidate's MOST RECENT question was:
"{last_question}"

The candidate's MOST RECENT answer (transcribed from speech) was:
"{last_answer}"

Earlier answers for context:
{previous_answers}

Decide the next question using this rule:
1. If the candidate's MOST RECENT answer contains something specific worth probing — a claim, a technology, a project, a decision, a trade-off, or a gap/weakness — ask a CROSS-QUESTION that digs deeper into THAT specific thing. Reference what they actually said (e.g. "You mentioned you used X — how did you handle Y?"). This is the preferred behavior whenever the answer gives you material.
2. Only if the most recent answer is empty, off-topic, or fully exhausted, move on to a NEW area relevant to the resume, category and difficulty.

Hard rules:
- The question MUST be different from every previously asked question above. Do NOT repeat the same topic if it was already fully covered.
- Ask exactly ONE question. Do not stack multiple questions.
- Match the difficulty ({difficulty}): Easy=fundamentals, Medium=practical/project depth, Hard=advanced design/trade-offs/problem solving.
- Sound conversational and human. Do NOT provide or hint at the answer.

Return ONLY valid JSON in this exact shape:
{{
  "question": "the question text",
  "category": "{category}",
  "difficulty": "{difficulty}",
  "question_type": "follow_up"
}}"""


def _fallback_question(
    category: str, difficulty: str, is_first: bool, previous_questions: List[str]
) -> dict:
    """Deterministic, resume-agnostic questions used only when Gemini is unavailable."""
    bank = {
        "initial": "To start, could you tell me a little about yourself and your background?",
        "generic": [
            f"Can you describe a {category} project you are proud of and your role in it?",
            "What was the most challenging technical problem you faced, and how did you solve it?",
            "How do you approach debugging when something isn't working as expected?",
            "Which tools or technologies are you most comfortable with, and why?",
            "How do you keep your skills up to date in a fast-moving field?",
            "Tell me about a time you had to learn something new quickly for a project.",
        ],
    }
    qtype = "initial" if is_first else "follow_up"
    if is_first:
        return {
            "question": bank["initial"],
            "category": category,
            "difficulty": difficulty,
            "question_type": qtype,
        }
    used = set(previous_questions)
    for q in bank["generic"]:
        if q not in used:
            return {
                "question": q,
                "category": category,
                "difficulty": difficulty,
                "question_type": qtype,
            }
    return {
        "question": "Is there anything else about your experience you'd like to highlight?",
        "category": category,
        "difficulty": difficulty,
        "question_type": qtype,
    }


def _generate(
    resume: Optional[Dict[str, Any]],
    category: str,
    difficulty: str,
    previous_questions: List[str],
    previous_answers: List[str],
    context: str,
    is_first: bool,
) -> dict:
    qtype = "initial" if is_first else "follow_up"
    if is_first:
        prompt = QUESTION_PROMPT.format(
            resume=_resume_to_text(resume),
            category=category,
            difficulty=difficulty,
            previous_questions="None",
            previous_answers="None",
            context=context or "Beginning of the interview.",
            qtype=qtype,
        )
    else:
        # Cross-questioning: focus on the candidate's most recent answer.
        last_question = previous_questions[-1] if previous_questions else ""
        last_answer = previous_answers[-1] if previous_answers else ""
        if not (last_answer or "").strip():
            last_answer = "(no answer was captured for the previous question)"
        earlier_answers = previous_answers[:-1] if len(previous_answers) > 1 else []
        prompt = FOLLOWUP_PROMPT.format(
            resume=_resume_to_text(resume),
            category=category,
            difficulty=difficulty,
            previous_questions="\n".join(f"- {q}" for q in previous_questions) or "None",
            previous_answers="\n".join(f"- {a}" for a in earlier_answers) or "None",
            last_question=last_question,
            last_answer=last_answer,
        )
    raw = _call_gemini(prompt)
    parsed = _extract_json(raw) if raw else None

    if parsed and parsed.get("question"):
        return {
            "question": str(parsed.get("question")).strip(),
            "category": parsed.get("category", category),
            "difficulty": parsed.get("difficulty", difficulty),
            "question_type": parsed.get("question_type", qtype),
        }

    # Recover a plausible question from raw prose if JSON failed.
    if raw:
        line = raw.strip().splitlines()[0].strip().strip('"')
        if line and len(line) > 10 and "{" not in line:
            return {
                "question": line,
                "category": category,
                "difficulty": difficulty,
                "question_type": qtype,
            }

    return _fallback_question(category, difficulty, is_first, previous_questions)


def generate_question(
    resume: Optional[Dict[str, Any]],
    category: str,
    difficulty: str,
    context: str = "",
) -> dict:
    """Generate the very first interview question."""
    return _generate(
        resume=resume,
        category=category,
        difficulty=difficulty,
        previous_questions=[],
        previous_answers=[],
        context=context,
        is_first=True,
    )


def generate_follow_up_question(
    resume: Optional[Dict[str, Any]],
    category: str,
    difficulty: str,
    previous_questions: List[str],
    previous_answers: List[str],
    context: str = "",
) -> dict:
    """Generate the next (dynamic / follow-up) question from the conversation so far."""
    return _generate(
        resume=resume,
        category=category,
        difficulty=difficulty,
        previous_questions=previous_questions,
        previous_answers=previous_answers,
        context=context,
        is_first=False,
    )


# ----------------------------------------------------------------------------
# Answer evaluation
# ----------------------------------------------------------------------------
EVAL_PROMPT = """You are an experienced technical interviewer evaluating a candidate's answer.

Interview Category: {category}
Difficulty: {difficulty}

Question:
{question}

Candidate's Answer (transcribed from speech):
{answer}

Rate the ANSWER QUALITY ONLY (ignore delivery/voice/video) on a 0-10 scale for each:
- technical_score: technical correctness and accuracy.
- relevance_score: how well it answers the question asked.
- completeness_score: coverage and depth of the response.
- clarity_score: how clearly the idea is communicated in the words used.

Also give one short constructive remark (max 2 sentences).

Return ONLY valid JSON:
{{
  "technical_score": 0-10,
  "relevance_score": 0-10,
  "completeness_score": 0-10,
  "clarity_score": 0-10,
  "remarks": "short remark"
}}"""


def evaluate_answer(
    question: str,
    answer: str,
    category: str,
    difficulty: str,
) -> dict:
    """Return answer-quality sub-scores (0-10) plus a remark."""
    default = {
        "technical_score": 5.0,
        "relevance_score": 5.0,
        "completeness_score": 5.0,
        "clarity_score": 5.0,
        "remarks": "Answer recorded. Automatic quality scoring was unavailable.",
    }

    if not answer or not answer.strip():
        return {
            "technical_score": 0.0,
            "relevance_score": 0.0,
            "completeness_score": 0.0,
            "clarity_score": 0.0,
            "remarks": "No answer was provided.",
        }

    prompt = EVAL_PROMPT.format(
        category=category,
        difficulty=difficulty,
        question=question,
        answer=answer,
    )
    raw = _call_gemini(prompt)
    parsed = _extract_json(raw) if raw else None
    if not parsed:
        return default

    def clamp(v: Any) -> float:
        try:
            return max(0.0, min(10.0, float(v)))
        except Exception:
            return 5.0

    return {
        "technical_score": clamp(parsed.get("technical_score", 5)),
        "relevance_score": clamp(parsed.get("relevance_score", 5)),
        "completeness_score": clamp(parsed.get("completeness_score", 5)),
        "clarity_score": clamp(parsed.get("clarity_score", 5)),
        "remarks": str(parsed.get("remarks", default["remarks"]))[:500],
    }


# ----------------------------------------------------------------------------
# Final feedback
# ----------------------------------------------------------------------------
FEEDBACK_PROMPT = """You are an expert interview coach writing a final report for a candidate.

Interview Category: {category}
Difficulty: {difficulty}
Overall Score (0-100): {overall_score}

Aggregated metrics (0-100):
- Answer quality: {answer_quality}
- Communication: {communication}
- Eye contact: {eye_contact}
- Posture: {posture}
- Gestures / non-verbal: {gesture}

Question & answer highlights:
{transcript}

Write a personalized, encouraging but honest report.

Return ONLY valid JSON:
{{
  "summary": "2-4 sentence overall summary",
  "strengths": ["..."],
  "weaknesses": ["..."],
  "technical_improvements": ["..."],
  "communication_improvements": ["..."],
  "nonverbal_improvements": ["..."],
  "recommendations": ["..."],
  "practice_topics": ["..."]
}}"""


def _fallback_feedback(aggregate: Dict[str, float]) -> dict:
    strengths, weaknesses = [], []
    if aggregate.get("answer_quality", 0) >= 60:
        strengths.append("Solid answer quality on several questions.")
    else:
        weaknesses.append("Answers could be more complete and technically detailed.")
    if aggregate.get("communication", 0) >= 60:
        strengths.append("Clear verbal communication with good pacing.")
    else:
        weaknesses.append("Watch speaking pace and reduce filler words.")
    if aggregate.get("eye_contact", 0) >= 60:
        strengths.append("Maintained reasonable eye contact with the camera.")
    else:
        weaknesses.append("Try to look at the camera more consistently.")
    return {
        "summary": "Here is a summary of your interview performance based on the "
        "metrics we captured. Keep practicing to improve further.",
        "strengths": strengths or ["Completed the interview end to end."],
        "weaknesses": weaknesses or ["Aim for deeper, structured answers."],
        "technical_improvements": [
            "Explain the 'why' behind your technical choices.",
            "Use concrete examples from your projects.",
        ],
        "communication_improvements": [
            "Structure answers using the STAR method where relevant.",
            "Reduce filler words such as 'um' and 'like'.",
        ],
        "nonverbal_improvements": [
            "Maintain steady eye contact with the camera.",
            "Sit upright and keep a confident posture.",
        ],
        "recommendations": [
            "Record and review a few practice answers.",
            "Prepare 2-3 strong project stories in advance.",
        ],
        "practice_topics": ["Core concepts for your role", "Behavioral STAR stories"],
    }


def generate_feedback(
    category: str,
    difficulty: str,
    overall_score: float,
    aggregate: Dict[str, float],
    transcript: str,
) -> dict:
    """Generate the final personalized feedback report."""
    prompt = FEEDBACK_PROMPT.format(
        category=category,
        difficulty=difficulty,
        overall_score=round(overall_score, 1),
        answer_quality=round(aggregate.get("answer_quality", 0), 1),
        communication=round(aggregate.get("communication", 0), 1),
        eye_contact=round(aggregate.get("eye_contact", 0), 1),
        posture=round(aggregate.get("posture", 0), 1),
        gesture=round(aggregate.get("gesture", 0), 1),
        transcript=transcript[:6000] or "No transcript available.",
    )
    raw = _call_gemini(prompt)
    parsed = _extract_json(raw) if raw else None
    if not parsed:
        return _fallback_feedback(aggregate)

    def as_list(v: Any) -> List[str]:
        if isinstance(v, list):
            return [str(x) for x in v]
        if isinstance(v, str) and v.strip():
            return [v.strip()]
        return []

    fb = _fallback_feedback(aggregate)
    return {
        "summary": str(parsed.get("summary") or fb["summary"]),
        "strengths": as_list(parsed.get("strengths")) or fb["strengths"],
        "weaknesses": as_list(parsed.get("weaknesses")) or fb["weaknesses"],
        "technical_improvements": as_list(parsed.get("technical_improvements"))
        or fb["technical_improvements"],
        "communication_improvements": as_list(parsed.get("communication_improvements"))
        or fb["communication_improvements"],
        "nonverbal_improvements": as_list(parsed.get("nonverbal_improvements"))
        or fb["nonverbal_improvements"],
        "recommendations": as_list(parsed.get("recommendations")) or fb["recommendations"],
        "practice_topics": as_list(parsed.get("practice_topics")) or fb["practice_topics"],
    }


def structure_resume_text(raw_text: str) -> Optional[dict]:
    """Ask Gemini to structure raw resume text into fields. Returns None if unavailable."""
    if not raw_text.strip():
        return None
    prompt = """Extract structured information from the following resume text.

Resume text:
{text}

Return ONLY valid JSON with these keys (use empty arrays/strings when unknown):
{{
  "name": "",
  "email": "",
  "summary": "",
  "education": ["..."],
  "skills": ["..."],
  "programming_languages": ["..."],
  "frameworks": ["..."],
  "technologies": ["..."],
  "projects": ["..."],
  "internships": ["..."],
  "certifications": ["..."],
  "experience": ["..."]
}}""".format(text=raw_text[:8000])
    raw = _call_gemini(prompt)
    return _extract_json(raw) if raw else None
