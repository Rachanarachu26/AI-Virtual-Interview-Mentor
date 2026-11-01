@echo off
REM One-command backend runner (Windows).
cd /d "%~dp0"

echo ==^> Setting up Python virtual environment...
python -m venv .venv
call .venv\Scripts\activate.bat

echo ==^> Installing backend dependencies (this can take several minutes the first time)...
python -m pip install --quiet --upgrade pip
echo setuptools^<81> .pip-constraints.txt
set PIP_CONSTRAINT=.pip-constraints.txt
pip install -r requirements.txt
set PIP_CONSTRAINT=
del .pip-constraints.txt

echo ==^> Starting FastAPI on http://localhost:8000  (docs at /docs)
uvicorn app.main:app --reload --port 8000
