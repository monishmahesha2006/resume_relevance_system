@echo off
echo Starting Resume Relevance System...
echo.

echo [1/3] Running Main Pipeline...
python main_simple.py
echo.

echo [2/3] Starting API Server...
start "API Server" cmd /k "cd backend && python api.py"
timeout /t 3 /nobreak >nul

echo [3/3] Starting Frontend Dashboard...
start "Frontend" cmd /k "cd frontend && streamlit run app.py"
timeout /t 3 /nobreak >nul

echo.
echo ✅ Resume Relevance System Started!
echo.
echo 🌐 Access Points:
echo    Frontend Dashboard: http://localhost:8501
echo    API Documentation: http://localhost:8000/docs
echo.
echo Press any key to exit...
pause >nul
