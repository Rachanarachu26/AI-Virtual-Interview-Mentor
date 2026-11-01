"""Interview-related Pydantic schemas."""
from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class InterviewCreate(BaseModel):
    category: str
    difficulty: str = Field(..., pattern="^(Easy|Medium|Hard)$")
    resume_id: Optional[int] = None
    total_questions: int = Field(default=5, ge=3, le=30)


class QuestionOut(BaseModel):
    id: int
    order_index: int
    question_text: str
    category: Optional[str] = None
    difficulty: Optional[str] = None
    question_type: str

    model_config = {"from_attributes": True}


class InterviewOut(BaseModel):
    id: int
    user_id: int
    resume_id: Optional[int] = None
    category: str
    difficulty: str
    total_questions: int
    status: str
    overall_score: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class NextQuestionRequest(BaseModel):
    """Optionally passed when requesting the next question (no body required)."""
    pass


class NextQuestionResponse(BaseModel):
    question: QuestionOut
    question_number: int
    total_questions: int
    is_last: bool


class AnswerSubmit(BaseModel):
    question_id: int
    transcript: str = ""
    # Speech metrics (from /api/speech/transcribe).
    speech_metrics: Optional[dict] = None
    # Vision metrics (from /api/vision/analyze). May be None if CV failed.
    vision_metrics: Optional[dict] = None


class EvaluationOut(BaseModel):
    id: int
    technical_score: float
    relevance_score: float
    completeness_score: float
    clarity_score: float
    answer_quality_score: float
    communication_score: float
    eye_contact_score: float
    posture_score: float
    gesture_score: float
    overall_score: float
    remarks: Optional[str] = None

    model_config = {"from_attributes": True}


class AnswerResult(BaseModel):
    answer_id: int
    evaluation: EvaluationOut


class FeedbackOut(BaseModel):
    summary: Optional[str] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    technical_improvements: Optional[List[str]] = None
    communication_improvements: Optional[List[str]] = None
    nonverbal_improvements: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None
    practice_topics: Optional[List[str]] = None
    overall_score: float = 0.0

    model_config = {"from_attributes": True}


class QAResult(BaseModel):
    question: str
    question_type: str
    transcript: Optional[str] = None
    evaluation: Optional[EvaluationOut] = None
    speech_metrics: Optional[Any] = None
    vision_metrics: Optional[Any] = None


class ResultsOut(BaseModel):
    interview: InterviewOut
    feedback: Optional[FeedbackOut] = None
    qa: List[QAResult] = []
    aggregate: dict = {}


class HistoryItem(BaseModel):
    id: int
    category: str
    difficulty: str
    status: str
    overall_score: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}
