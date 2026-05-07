Write-Host "Iniciando Py-Fit Web Dashboard..." -ForegroundColor Green

# Caminho para o Python do ambiente virtual
$PYTHON_PATH = ".\.venv\Scripts\python.exe"

# Verifica se o ambiente virtual existe
if (-not (Test-Path $PYTHON_PATH)) {
    Write-Host "Ambiente virtual não encontrado! Criando..." -ForegroundColor Yellow
    python -m venv .venv
    Write-Host "Instalando dependências do backend..." -ForegroundColor Gray
    & $PYTHON_PATH -m pip install -r api/requirements.txt
}

# Inicia a API FastAPI em uma nova janela
Write-Host "Iniciando API (Backend) na porta 8000..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit -Command `"& '$PYTHON_PATH' -m uvicorn api.main:app --reload --port 8000`""

# Verifica dependências do frontend
if (-not (Test-Path "web\node_modules")) {
    Write-Host "Dependências do frontend não encontradas! Instalando..." -ForegroundColor Yellow
    Push-Location web
    npm install
    Pop-Location
}

# Inicia o Frontend Vite em uma nova janela
Write-Host "Iniciando Frontend (Vite) na porta 5173..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit -Command `"cd web; npm run dev`""

Write-Host "Processos iniciados!" -ForegroundColor Green
Write-Host "Aguardando inicialização para abrir o navegador..." -ForegroundColor Gray
Start-Sleep -Seconds 5

# Tenta abrir o navegador no frontend
Start-Process "http://localhost:5173"

Write-Host "Pronto! Se o navegador não abrir, acesse: http://localhost:5173" -ForegroundColor White
