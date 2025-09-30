@echo off
echo Starting AI Calling Agent - Full Stack...
echo.

echo ============================================
echo Starting Backend (FastAPI)...
echo ============================================
start /b cmd /c "start-backend.bat"

echo Waiting for backend to initialize...
timeout /t 5 /nobreak >nul

echo.
echo ============================================
echo Starting Frontend (React + Vite)...
echo ============================================
start /b cmd /c "start-frontend.bat"

echo.
echo ============================================
echo Both services are starting...
echo ============================================
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo Press any key to stop all services...
pause >nul

echo.
echo Stopping services...
taskkill /f /im "python.exe" >nul 2>&1
taskkill /f /im "node.exe" >nul 2>&1
echo Services stopped.

pause