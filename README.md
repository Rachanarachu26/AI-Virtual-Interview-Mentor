# 🎙️ AI Virtual Interview Mentor

An AI-powered virtual interview platform. Upload your resume, pick a role and
difficulty, and sit through a **realistic spoken interview** conducted by an AI
interviewer. Get instant, personalized feedback on **what you said** (answer
quality), **how you said it** (speech/communication), and **how you showed up on
camera** (non-verbal behavior).

The AI interviewer **speaks every question aloud** (Text-to-Speech), listens to
your spoken answer (Whisper speech-to-text), watches your body language
(MediaPipe computer vision), and scores everything with a weighted evaluation
engine — with questions generated dynamically by **Google Gemini**.

---

## ✨ Features

- 🔐 Register / login with JWT auth and hashed passwords
- 📄 Resume upload (PDF) + parsing with PyMuPDF (+ optional Gemini structuring)
- 🧠 **Dynamic** question generation with Gemini (never a fixed list)
- 🔁 Follow-up questions based on your previous answers
- 🔊 AI interviewer **speaks** each question (Web Speech API TTS)
- 🎤 Answer by microphone → Whisper transcription + communication metrics
- 🎥 Webcam analysis (eye contact, posture, head movement, gestures) via MediaPipe
- 📊 Weighted Performance Evaluation Engine (answer quality + speech + vision)
- 📝 Personalized final report: strengths, weaknesses, suggestions
- 🗂️ Interview history and detailed per-question reports

---

## 🧱 Tech Stack

**Frontend:** React + Vite (JavaScript), React Router, Axios, Web Speech API
**Backend:** FastAPI, Uvicorn, SQLAlchemy, Pydantic
**Database:** MySQL (via PyMySQL + SQLAlchemy ORM)
**AI / LLM:** Google Gemini (official `google-genai` SDK)
**Speech:** OpenAI Whisper (local, speech-to-text only)
**Computer Vision:** MediaPipe Holistic + OpenCV

---

## 📁 Project Structure

```
ai-interview-mentor/
├── frontend/            # React + Vite app
│   └── src/
│       ├── components/  # Navbar, ScoreRing, ScoreBar, Loader, Steps, ...
│       ├── pages/       # Landing, Login, Dashboard, LiveInterview, Results, ...
│       ├── hooks/       # useSpeech (TTS), useMediaCapture (cam/mic)
│       ├── context/     # AuthContext
│       ├── services/    # api.js (axios)
│       └── utils/
├── backend/             # FastAPI app
│   └── app/
│       ├── api/         # auth, resume, interviews, speech, vision
│       ├── models/      # SQLAlchemy models
│       ├── schemas/     # Pydantic schemas
│       ├── services/    # gemini, resume, speech, vision, evaluation, feedback, tts
│       ├── core/        # config, security, dependencies
│       └── database/    # database.py, init_db.py
├── README.md
└── .gitignore
```

---

## 🚀 Getting Started

You can run this **two ways**. Docker is by far the easiest — it bundles MySQL
so you don't install anything except Docker.

---

## 🐳 Option A — Docker (recommended, easiest)

**Only prerequisite:** [Docker Desktop](https://www.docker.com/products/docker-desktop/)
installed and running. No need to install Python, Node, MySQL, or FFmpeg — the
containers include everything.

```bash
# From the project root (the folder with docker-compose.yml):
docker compose up --build
```

Then open **http://localhost:8080** in **Google Chrome**.

- The first build is large (Whisper/PyTorch + MediaPipe) and downloads a few GB —
  give it several minutes. Subsequent starts are fast.
- MySQL runs in its own container automatically — **no database setup needed**.
- The Gemini API key is already set in `backend/.env`, so it works out of the box.
- To stop: press `Ctrl+C`, then `docker compose down` (add `-v` to also wipe the
  database volume).

| Service | URL |
| --- | --- |
| App (frontend) | http://localhost:8080 |
| API docs | http://localhost:8000/docs |

---

## 💻 Option B — Run locally without Docker

### Prerequisites

- **Python 3.10 – 3.11** (recommended for MediaPipe / Whisper compatibility)
- **Node.js 18+**
- **MySQL** running locally
- **FFmpeg** installed (required by Whisper for audio decoding)
  - macOS: `brew install ffmpeg`
  - Windows: download from ffmpeg.org and add to PATH
  - Linux: `sudo apt install ffmpeg`
- A **Google Gemini API key** (https://aistudio.google.com/apikey)

---

### 1) Create the database & set your MySQL credentials

Start MySQL, then create the database:

```sql
CREATE DATABASE ai_interview CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

> ⚠️ **Important — set your own MySQL login.** Open `backend/.env` and edit
> `DATABASE_URL` to match YOUR MySQL username/password/host. The default is:
>
> ```
> DATABASE_URL=mysql+pymysql://root:@localhost:3306/ai_interview
> ```
>
> That is `root` with an **empty** password. If your MySQL `root` has a
> password, use `mysql+pymysql://root:YOURPASSWORD@localhost:3306/ai_interview`.
> The `GEMINI_API_KEY` is already filled in for you in `backend/.env`.

---

### 2) Backend — one command

**macOS / Linux:**
```bash
cd backend
./run.sh
```

**Windows:**
```bat
cd backend
run.bat
```

That creates a virtual environment, installs everything, and starts the API on
**http://localhost:8000** (docs at `/docs`).

<details>
<summary>Prefer to run it manually? (click)</summary>

```bash
cd backend
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
</details>

> The first backend install is large (Whisper/PyTorch + MediaPipe) and can take
> several minutes. The first speech transcription also downloads the Whisper
> model (`WHISPER_MODEL`, default `base`) once.

---

### 3) Frontend — one command (in a second terminal)

**macOS / Linux:**
```bash
cd frontend
./run.sh
```

**Windows:**
```bat
cd frontend
run.bat
```

Or manually: `cd frontend && npm install && npm run dev`.

Open **http://localhost:5173** in **Google Chrome** (recommended — the live
answer transcription uses Chrome's Web Speech API). The Vite dev server proxies
`/api` to the FastAPI backend on port 8000 (configured in `vite.config.js`).

---

## 🔑 Environment Variables (`backend/.env`)

| Variable | Description | Example |
| --- | --- | --- |
| `DATABASE_URL` | MySQL connection string | `mysql+pymysql://root:password@localhost:3306/ai_interview` |
| `JWT_SECRET_KEY` | Secret for signing JWTs | `change_this_secret` |
| `GEMINI_API_KEY` | Google Gemini API key | `your_gemini_api_key` |
| `GEMINI_MODEL` | Gemini model id | `gemini-3.6-flash` |
| `WHISPER_MODEL` | Whisper size (`tiny`…`large`) | `base` |
| `CORS_ORIGINS` | Allowed frontend origins | `http://localhost:5173` |
| `WEIGHT_*` | Evaluation weights (sum ≈ 1.0) | see `.env.example` |

**Secrets never reach the frontend** — Gemini and JWT keys live only in the backend.

---

## 🧮 How Scoring Works

The **Performance Evaluation Engine** combines three sources into a weighted score:

```
overall = answer_quality * 0.40
        + communication  * 0.25
        + eye_contact    * 0.15
        + posture        * 0.10
        + gesture_score  * 0.10
```

- **Gemini** evaluates the *semantic and technical quality* of each answer
  (technical, relevance, completeness, clarity — 0–10 each).
- **Whisper + speech metrics** provide *communication* signals (WPM, filler
  words, answer length).
- **MediaPipe + OpenCV** provide *non-verbal* signals (eye contact, posture,
  head stability, gestures) derived from detected landmarks.

Weights are configurable in `.env`. If computer vision is unavailable for an
answer, its weight is redistributed so you are not unfairly penalized — the
interview always continues.

> Note: there is **no separate trained ML "performance model."** Gemini scores
> answer quality; speech and vision modules provide the other metrics; the
> engine combines them with a transparent weighted formula.

---

## 🔄 Interview Flow

```
Register → Login → Upload Resume → Parse Resume
   → Select Category → Select Difficulty → Start Interview
   → Gemini generates a question
   → TTS speaks it → you listen
   → Mic enabled → you answer
   → Whisper transcribes → speech + vision analysis
   → Gemini evaluates the answer
   → next / follow-up question (spoken) …
   → Final evaluation → Personalized feedback → Results report
```

---

## 🩹 Troubleshooting

- **Camera/Mic blocked:** the browser must grant permission; use `localhost`
  (secure context) so `getUserMedia` works.
- **No AI voice:** Web Speech API voices load asynchronously — the app falls
  back to on-screen text if speech synthesis isn't available.
- **Whisper errors:** ensure **FFmpeg** is installed and on your PATH.
- **MediaPipe install issues:** use Python 3.10/3.11; vision failures are
  handled gracefully and simply mark vision metrics as unavailable.
- **Gemini errors / no key:** the app degrades gracefully with fallback
  questions and neutral evaluations, but set `GEMINI_API_KEY` for the real
  dynamic experience.
- **DB connection errors:** confirm MySQL is running and `DATABASE_URL` is correct,
  then re-run `python -m app.database.init_db`.

---

## 📜 API Overview

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Log in (JWT) |
| POST | `/api/resume/upload` | Upload & parse PDF resume |
| GET | `/api/resume/{id}` | Fetch a resume |
| POST | `/api/interviews` | Create an interview |
| POST | `/api/interviews/{id}/question` | Generate next question (Gemini) |
| POST | `/api/interviews/{id}/answer` | Submit answer + metrics → evaluate |
| POST | `/api/interviews/{id}/complete` | Finalize + feedback |
| GET | `/api/interviews/{id}/results` | Full report |
| GET | `/api/interviews/history` | Interview history |
| POST | `/api/speech/transcribe` | Whisper transcription + metrics |
| POST | `/api/vision/analyze` | MediaPipe non-verbal metrics |

Full interactive docs at **http://localhost:8000/docs**.
