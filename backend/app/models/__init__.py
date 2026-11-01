"""Import all models so SQLAlchemy's metadata is aware of every table."""
from app.models.user import User
from app.models.resume import Resume
from app.models.interview import Interview
from app.models.question import Question
from app.models.answer import Answer
from app.models.speech_metrics import SpeechMetric
from app.models.vision_metrics import VisionMetric
from app.models.evaluation import Evaluation
from app.models.feedback import Feedback

__all__ = [
    "User",
    "Resume",
    "Interview",
    "Question",
    "Answer",
    "SpeechMetric",
    "VisionMetric",
    "Evaluation",
    "Feedback",
]
