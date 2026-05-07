Write-Host "Iniciando Py-Fit Web Dashboard..." -ForegroundColor Green

# Inicia a API FastAPI
Write-Host "Iniciando API (Backend)..."
Start-Process powershell -ArgumentList "-NoExit -Command `"python -m uvicorn api.main:app --reload --port 8000`""

# Inicia o Frontend Vite
Write-Host "Iniciando Frontend (React)..."
Start-Process powershell -ArgumentList "-NoExit -Command `"cd web; npm run dev`""

Write-Host "Processos iniciados! O navegador deve abrir em instantes (ou acesse http://localhost:5173)." -ForegroundColor Cyan
