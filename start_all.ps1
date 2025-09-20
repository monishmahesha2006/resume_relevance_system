# Resume Relevance System Startup Script
Write-Host "🚀 Starting Resume Relevance System..." -ForegroundColor Green
Write-Host ""

# Step 1: Run Main Pipeline
Write-Host "[1/3] Running Main Pipeline..." -ForegroundColor Yellow
python main_simple.py
Write-Host ""

# Step 2: Start API Server
Write-Host "[2/3] Starting API Server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; python api.py"
Start-Sleep -Seconds 3

# Step 3: Start Frontend
Write-Host "[3/3] Starting Frontend Dashboard..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; streamlit run app.py"
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "✅ Resume Relevance System Started!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Access Points:" -ForegroundColor Cyan
Write-Host "   Frontend Dashboard: http://localhost:8501" -ForegroundColor White
Write-Host "   API Documentation: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
