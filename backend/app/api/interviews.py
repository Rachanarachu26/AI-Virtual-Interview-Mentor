"""Interview endpoints: create, dynamic questions, answers, results, history."""
import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.models.answer import Answer
from app.models.evaluation import Evaluation
from app.models.feedback import Feedback
from app.models.interview import Interview
from app.models.question import Question
from app.models.resume import Resume
from app.models.speech_metrics import SpeechMetric
from app.models.user import User
from app.models.vision_metrics import VisionMetric
from app.schemas.interview import (
    AnswerResult,
    AnswerSubmit,
    EvaluationOut,
    FeedbackOut,
    HistoryItem,
    InterviewCreate,
    InterviewOut,
    NextQuestionResponse,
    QAResult,
    QuestionOut,
    ResultsOut,
)
from app.services import (
    evaluation_service,
    feedback_service,
    gemini_service,
    speech_service,
    tts_service,
)

logger = logging.getLogger("interviews_api")

router = APIRouter(prefix="/api/interviews", tags=["interviews"])

CATEGORIES = [
    "Software Developer",
    "Frontend Developer",
    "Backend Developer",
    "Full Stack Developer",
    "Data Science",
    "Machine Learning",
    "General Technical",
    "HR / Behavioral",
]


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------
@router.get("/meta/categories")
def get_categories():
    return {"categories": CATEGORIES, "difficulties": ["Easy", "Medium", "Hard"]}


# ---------------------------------------------------------------------------
# History  (declared before /{id} so "history" is not treated as an id)
# ---------------------------------------------------------------------------
@router.get("/history", response_model=List[HistoryItem])
def interview_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Interview)
        .filter(Interview.user_id == current_user.id)
        .order_by(Interview.created_at.desc())
        .all()
    )


# ---------------------------------------------------------------------------
# Create interview
# ---------------------------------------------------------------------------
@router.post("", response_model=InterviewOut, status_code=status.HTTP_201_CREATED)
def create_interview(
    payload: InterviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.category not in CATEGORIES:
        raise HTTPException(status_code=400, detail="Unknown interview category.")

    resume_id = payload.resume_id
    if resume_id:
        resume = (
            db.query(Resume)
            .filter(Resume.id == resume_id, Resume.user_id == current_user.id)
            .first()
        )
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found.")
    else:
        # Fall back to the user's latest resume if any.
        resume = (
            db.query(Resume)
            .filter(Resume.user_id == current_user.id)
            .order_by(Resume.created_at.desc())
            .first()
        )
        resume_id = resume.id if resume else None

    interview = Interview(
        user_id=current_user.id,
        resume_id=resume_id,
        category=payload.category,
        difficulty=payload.difficulty,
        total_questions=payload.total_questions,
        status="in_progress",
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    return interview


def _get_interview_or_404(db: Session, interview_id: int, user: User) -> Interview:
    interview = (
        db.query(Interview)
        .filter(Interview.id == interview_id, Interview.user_id == user.id)
        .first()
    )
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found.")
    return interview


def _resume_dict(db: Session, interview: Interview) -> dict:
    if not interview.resume_id:
        return {}
    resume = db.query(Resume).filter(Resume.id == interview.resume_id).first()
    if not resume:
        return {}
    return {
        "name": resume.name,
        "summary": resume.summary,
        "education": resume.education,
        "skills": resume.skills,
        "programming_languages": resume.programming_languages,
        "frameworks": resume.frameworks,
        "technologies": resume.technologies,
        "projects": resume.projects,
        "internships": resume.internships,
        "certifications": resume.certifications,
        "experience": resume.experience,
    }


# ---------------------------------------------------------------------------
# Get single interview
# ---------------------------------------------------------------------------
@router.get("/{interview_id}", response_model=InterviewOut)
def get_interview(
    interview_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_interview_or_404(db, interview_id, current_user)


# ---------------------------------------------------------------------------
# Generate / fetch the next question (dynamic, via Gemini)
# ---------------------------------------------------------------------------
@router.post("/{interview_id}/question", response_model=NextQuestionResponse)
def next_question(
    interview_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    interview = _get_interview_or_404(db, interview_id, current_user)

    questions = (
        db.query(Question)
        .filter(Question.interview_id == interview.id)
        .order_by(Question.order_index.asc())
        .all()
    )

    # If the last question has not been answered yet, return it (idempotent).
    if questions:
        last = questions[-1]
        answered = (
            db.query(Answer).filter(Answer.question_id == last.id).first() is not None
        )
        if not answered:
            return NextQuestionResponse(
                question=QuestionOut.model_validate(last),
                question_number=last.order_index + 1,
                total_questions=interview.total_questions,
                is_last=(last.order_index + 1) >= interview.total_questions,
            )

    if len(questions) >= interview.total_questions:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="All questions for this interview have been asked.",
        )

    resume = _resume_dict(db, interview)
    prev_qs = [q.question_text for q in questions]
    prev_as = [
        (q.answer.transcript if q.answer else "") or "" for q in questions
    ]
    context = (
        f"This is question {len(questions) + 1} of {interview.total_questions}."
    )

    q_no = len(questions) + 1
    if not questions:
        logger.info(
            "[interview %s] STEP 1/2  Generating INITIAL question (%s / %s) via Gemini  [Q%s of %s]",
            interview.id, interview.category, interview.difficulty, q_no, interview.total_questions,
        )
        result = gemini_service.generate_question(
            resume=resume,
            category=interview.category,
            difficulty=interview.difficulty,
            context="Beginning of the interview.",
        )
    else:
        logger.info(
            "[interview %s] STEP 1/2  Generating FOLLOW-UP question via Gemini "
            "(using %s previous Q&A)  [Q%s of %s]",
            interview.id, len(questions), q_no, interview.total_questions,
        )
        result = gemini_service.generate_follow_up_question(
            resume=resume,
            category=interview.category,
            difficulty=interview.difficulty,
            previous_questions=prev_qs,
            previous_answers=prev_as,
            context=context,
        )

    question = Question(
        interview_id=interview.id,
        order_index=len(questions),
        question_text=result["question"],
        category=result.get("category", interview.category),
        difficulty=result.get("difficulty", interview.difficulty),
        question_type=result.get("question_type", "initial" if not questions else "follow_up"),
    )
    db.add(question)
    db.commit()
    db.refresh(question)

    logger.info(
        "[interview %s] STEP 2/2  Question ready (%s): %r",
        interview.id, question.question_type, question.question_text[:90],
    )

    return NextQuestionResponse(
        question=QuestionOut.model_validate(question),
        question_number=question.order_index + 1,
        total_questions=interview.total_questions,
        is_last=(question.order_index + 1) >= interview.total_questions,
    )


# ---------------------------------------------------------------------------
# Submit an answer (transcript + speech + vision) -> evaluate
# ---------------------------------------------------------------------------
@router.post("/{interview_id}/answer", response_model=AnswerResult)
def submit_answer(
    interview_id: int,
    payload: AnswerSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    interview = _get_interview_or_404(db, interview_id, current_user)

    question = (
        db.query(Question)
        .filter(
            Question.id == payload.question_id,
            Question.interview_id == interview.id,
        )
        .first()
    )
    if not question:
        raise HTTPException(status_code=404, detail="Question not found.")

    existing = db.query(Answer).filter(Answer.question_id == question.id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This question has already been answered.",
        )

    transcript = (payload.transcript or "").strip()
    logger.info(
        "[interview %s] STEP 1/4  Answer received for Q%s  (%s chars transcript)",
        interview.id, question.order_index + 1, len(transcript),
    )

    answer = Answer(
        interview_id=interview.id,
        question_id=question.id,
        transcript=transcript,
    )
    db.add(answer)
    db.flush()  # get answer.id without committing yet

    # ---- Speech metrics ----
    speech = payload.speech_metrics or {}
    if not speech and transcript:
        speech = speech_service.compute_metrics(transcript, 0.0)
    sm = SpeechMetric(
        answer_id=answer.id,
        word_count=speech.get("word_count", 0),
        speaking_duration=speech.get("speaking_duration", 0.0),
        words_per_minute=speech.get("words_per_minute", 0.0),
        filler_word_count=speech.get("filler_word_count", 0),
        filler_word_frequency=speech.get("filler_word_frequency", 0.0),
        filler_words_detail=speech.get("filler_words_detail", {}),
        pause_count=speech.get("pause_count", 0),
        answer_length=speech.get("answer_length", len(transcript)),
        communication_score=speech.get("communication_score", 0.0),
    )
    db.add(sm)

    # ---- Vision metrics ----
    vision = payload.vision_metrics or {}
    vm = VisionMetric(
        answer_id=answer.id,
        available=bool(vision.get("available", False)),
        eye_contact_percentage=vision.get("eye_contact_percentage", 0.0),
        posture_score=vision.get("posture_score", 0.0),
        head_movement_score=vision.get("head_movement_score", 0.0),
        gesture_score=vision.get("gesture_score", 0.0),
        frames_analyzed=vision.get("frames_analyzed", 0),
    )
    db.add(vm)
    logger.info(
        "[interview %s] STEP 2/4  Speech metrics: %s words, %s WPM, %s fillers, comm=%s"
        "  |  Vision: %s",
        interview.id, speech.get("word_count", 0), speech.get("words_per_minute", 0),
        speech.get("filler_word_count", 0), speech.get("communication_score", 0),
        "available" if vision.get("available") else "unavailable",
    )

    # ---- Answer quality (Gemini) ----
    logger.info("[interview %s] STEP 3/4  Evaluating answer quality via Gemini...", interview.id)
    quality = gemini_service.evaluate_answer(
        question=question.question_text,
        answer=transcript,
        category=interview.category,
        difficulty=interview.difficulty,
    )

    # ---- Combine into final scores ----
    combined = evaluation_service.combine_scores(quality, speech, vision)

    evaluation = Evaluation(
        interview_id=interview.id,
        answer_id=answer.id,
        technical_score=combined["technical_score"],
        relevance_score=combined["relevance_score"],
        completeness_score=combined["completeness_score"],
        clarity_score=combined["clarity_score"],
        answer_quality_score=combined["answer_quality_score"],
        communication_score=combined["communication_score"],
        eye_contact_score=combined["eye_contact_score"],
        posture_score=combined["posture_score"],
        gesture_score=combined["gesture_score"],
        overall_score=combined["overall_score"],
        remarks=combined.get("remarks", ""),
    )
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)

    logger.info(
        "[interview %s] STEP 4/4  Scored answer  ->  quality=%s  comm=%s  overall=%s / 100",
        interview.id, combined["answer_quality_score"],
        combined["communication_score"], combined["overall_score"],
    )

    return AnswerResult(
        answer_id=answer.id,
        evaluation=EvaluationOut.model_validate(evaluation),
    )


# ---------------------------------------------------------------------------
# Results (finalizes the interview + feedback on first call)
# ---------------------------------------------------------------------------
def _finalize_interview(db: Session, interview: Interview) -> None:
    evaluations = (
        db.query(Evaluation).filter(Evaluation.interview_id == interview.id).all()
    )
    aggregate = evaluation_service.aggregate_interview(evaluations)

    # Build Q/A pairs for the feedback prompt.
    questions = (
        db.query(Question)
        .filter(Question.interview_id == interview.id)
        .order_by(Question.order_index.asc())
        .all()
    )
    qa_pairs = []
    for q in questions:
        ev = q.answer.evaluation if (q.answer and q.answer.evaluation) else None
        qa_pairs.append(
            {
                "question": q.question_text,
                "transcript": q.answer.transcript if q.answer else "",
                "evaluation": {
                    "answer_quality_score": ev.answer_quality_score if ev else 0,
                    "communication_score": ev.communication_score if ev else 0,
                }
                if ev
                else None,
            }
        )

    overall = aggregate["overall"]
    interview.overall_score = overall
    interview.status = "completed"
    interview.completed_at = datetime.utcnow()

    # Generate + store feedback (only if not already present).
    existing_fb = (
        db.query(Feedback).filter(Feedback.interview_id == interview.id).first()
    )
    if not existing_fb:
        logger.info(
            "[interview %s] FINALIZE  Overall score = %s / 100. Generating final "
            "feedback report via Gemini...", interview.id, overall,
        )
        fb_data = feedback_service.generate_final_feedback(
            category=interview.category,
            difficulty=interview.difficulty,
            overall_score=overall,
            aggregate=aggregate,
            qa_pairs=qa_pairs,
        )
        feedback = Feedback(
            interview_id=interview.id,
            summary=fb_data.get("summary"),
            strengths=fb_data.get("strengths"),
            weaknesses=fb_data.get("weaknesses"),
            technical_improvements=fb_data.get("technical_improvements"),
            communication_improvements=fb_data.get("communication_improvements"),
            nonverbal_improvements=fb_data.get("nonverbal_improvements"),
            recommendations=fb_data.get("recommendations"),
            practice_topics=fb_data.get("practice_topics"),
            overall_score=overall,
        )
        db.add(feedback)

    db.commit()
    logger.info("[interview %s] FINALIZE  Interview completed and report stored.", interview.id)


@router.post("/{interview_id}/complete", response_model=ResultsOut)
def complete_interview(
    interview_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    interview = _get_interview_or_404(db, interview_id, current_user)
    if interview.status != "completed":
        _finalize_interview(db, interview)
        db.refresh(interview)
    return _build_results(db, interview)


@router.get("/{interview_id}/results", response_model=ResultsOut)
def get_results(
    interview_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    interview = _get_interview_or_404(db, interview_id, current_user)

    # Finalize on first view if there is at least one answer and it isn't done.
    if interview.status != "completed":
        answered = (
            db.query(Answer).filter(Answer.interview_id == interview.id).count()
        )
        if answered > 0:
            _finalize_interview(db, interview)
            db.refresh(interview)

    return _build_results(db, interview)


def _build_results(db: Session, interview: Interview) -> ResultsOut:
    questions = (
        db.query(Question)
        .filter(Question.interview_id == interview.id)
        .order_by(Question.order_index.asc())
        .all()
    )
    qa: List[QAResult] = []
    for q in questions:
        ans = q.answer
        ev = ans.evaluation if ans else None
        sm = ans.speech_metric if ans else None
        vm = ans.vision_metric if ans else None
        qa.append(
            QAResult(
                question=q.question_text,
                question_type=q.question_type,
                transcript=ans.transcript if ans else None,
                evaluation=EvaluationOut.model_validate(ev) if ev else None,
                speech_metrics={
                    "word_count": sm.word_count,
                    "words_per_minute": sm.words_per_minute,
                    "filler_word_count": sm.filler_word_count,
                    "speaking_duration": sm.speaking_duration,
                    "communication_score": sm.communication_score,
                }
                if sm
                else None,
                vision_metrics={
                    "available": vm.available,
                    "eye_contact_percentage": vm.eye_contact_percentage,
                    "posture_score": vm.posture_score,
                    "head_movement_score": vm.head_movement_score,
                    "gesture_score": vm.gesture_score,
                }
                if vm
                else None,
            )
        )

    fb = db.query(Feedback).filter(Feedback.interview_id == interview.id).first()
    evaluations = (
        db.query(Evaluation).filter(Evaluation.interview_id == interview.id).all()
    )
    aggregate = evaluation_service.aggregate_interview(evaluations)

    return ResultsOut(
        interview=InterviewOut.model_validate(interview),
        feedback=FeedbackOut.model_validate(fb) if fb else None,
        qa=qa,
        aggregate=aggregate,
    )
