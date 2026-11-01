"""FastAPI application entry point for the AI Virtual Interview Mentor."""
import logging
import warnings

# Keep the log clean: hide third-party deprecation/SSL noise that clutters output.
warnings.filterwarnings("ignore")

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import auth, interviews, resume, speech, vision
from app.core.config import settings
from app.database.database import Base, engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)-16s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("main")

# Quiet noisy third-party loggers so the execution-step logs stand out.
logging.getLogger("google_genai").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# Ensure tables exist on startup (safe to call repeatedly).
import app.models  # noqa: F401  (registers models on Base.metadata)

app = FastAPI(
    title="AI Virtual Interview Mentor API",
    version="1.0.0",
    description="AI-powered virtual interview platform (Gemini + Whisper + MediaPipe).",
)

# ---- CORS ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables ensured.")
    except Exception as exc:
        # The API can still boot; DB-dependent endpoints will report errors.
        logger.error("Could not create tables on startup: %s", exc)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected server error occurred."},
    )


@app.get("/")
def root():
    return {"status": "ok", "service": "AI Virtual Interview Mentor"}


@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "gemini_model": settings.GEMINI_MODEL,
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "whisper_model": settings.WHISPER_MODEL,
    }


# ---- Routers ----
app.include_router(auth.router)
app.include_router(resume.router)
app.include_router(interviews.router)
app.include_router(speech.router)
app.include_router(vision.router)
