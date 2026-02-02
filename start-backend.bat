@echo off
echo Starting VideoExpress AI Backend...
echo.

cd backend

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Starting FastAPI server...
echo Backend will be available at: http://localhost:8000
echo Health check: http://localhost:8000/health
echo.

uvicorn main:app --reload --host 0.0.0.0 --port 8000
