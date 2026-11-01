@echo off
REM One-command frontend runner (Windows).
cd /d "%~dp0"

echo ==^> Installing frontend dependencies...
call npm install

echo ==^> Starting the app on http://localhost:5173
call npm run dev
