@echo off
echo Starting AI Calling Agent FastAPI Backend...
echo.

echo Checking if virtual environment exists...
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Checking if dependencies are installed...
pip show fastapi >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing backend dependencies...
    pip install -r requirements.txt
    echo.
)

echo.
echo Starting FastAPI server...
echo Backend will be available at: http://localhost:8000
echo API documentation available at: http://localhost:8000/docs
echo.

uvicorn webui.app:app --host 0.0.0.0 --port 8000 --reload

pause