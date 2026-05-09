# Start Multi-Provider Video Analysis System
# PowerShell Script for Windows

param(
    [string]$Mode = "dev",
    [int]$Port = 8080,
    [switch]$Test,
    [switch]$Help
)

function Write-Header {
    Write-Host "`n" -ForegroundColor Cyan
    Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║  AI Video Analysis Platform - Multi-Provider Aggregation   ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Info {
    param([string]$Message)
    Write-Host "  ℹ️  $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "  ✓ $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "  ✗ $Message" -ForegroundColor Red
}

function Write-Warning {
    param([string]$Message)
    Write-Host "  ⚠️  $Message" -ForegroundColor Yellow
}

function Show-Help {
    Write-Header
    Write-Host "USAGE:" -ForegroundColor Cyan
    Write-Host "  .\start_system.ps1 [Options]" -ForegroundColor White
    Write-Host ""
    Write-Host "OPTIONS:" -ForegroundColor Cyan
    Write-Host "  -Mode <dev|prod>     Development or production mode (default: dev)" -ForegroundColor White
    Write-Host "  -Port <number>       Port to run on (default: 8080)" -ForegroundColor White
    Write-Host "  -Test                Run tests instead of starting server" -ForegroundColor White
    Write-Host "  -Help                Show this help message" -ForegroundColor White
    Write-Host ""
    Write-Host "EXAMPLES:" -ForegroundColor Cyan
    Write-Host "  .\start_system.ps1                    # Start in dev mode" -ForegroundColor White
    Write-Host "  .\start_system.ps1 -Mode prod        # Start in production mode" -ForegroundColor White
    Write-Host "  .\start_system.ps1 -Port 5000        # Run on port 5000" -ForegroundColor White
    Write-Host "  .\start_system.ps1 -Test             # Run test suite" -ForegroundColor White
    Write-Host ""
}

function Check-Requirements {
    Write-Info "Checking system requirements..."
    
    # Check Python
    $python = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Python installed: $python"
    } else {
        Write-Error "Python not found. Please install Python 3.8+"
        return $false
    }
    
    # Check virtual environment
    $venv = ".venv"
    if (Test-Path $venv) {
        Write-Success "Virtual environment exists"
    } else {
        Write-Warning "Virtual environment not found, creating..."
        python -m venv $venv
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Virtual environment created"
        } else {
            Write-Error "Failed to create virtual environment"
            return $false
        }
    }
    
    return $true
}

function Activate-Environment {
    Write-Info "Activating virtual environment..."
    & ".\.venv\Scripts\Activate.ps1"
    Write-Success "Environment activated"
}

function Install-Dependencies {
    Write-Info "Installing dependencies..."
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Dependencies installed"
        return $true
    } else {
        Write-Error "Failed to install dependencies"
        return $false
    }
}

function Setup-Environment {
    Write-Info "Setting up environment..."
    
    # Check for .env file
    if (-not (Test-Path ".env")) {
        Write-Warning ".env file not found"
        if (Test-Path ".env.production") {
            Copy-Item ".env.production" ".env"
            Write-Success ".env created from template"
        } else {
            Write-Error ".env file required. Copy .env.production to .env and configure"
            return $false
        }
    } else {
        Write-Success ".env file exists"
    }
    
    return $true
}

function Initialize-Database {
    Write-Info "Initializing database..."
    python -c "from backend.database import Database; Database().init_db()" 2>$null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Database initialized"
        return $true
    } else {
        Write-Warning "Database initialization skipped (may already exist)"
        return $true
    }
}

function Start-Development {
    param([int]$Port)
    
    Write-Header
    Write-Info "Starting server in DEVELOPMENT mode..."
    Write-Info "Port: $Port"
    Write-Info "Mode: Development (Debug enabled)"
    Write-Info ""
    Write-Host "Server will open at http://127.0.0.1:$Port" -ForegroundColor Green
    Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
    Write-Host ""
    
    $env:FLASK_ENV = "development"
    $env:FLASK_DEBUG = "True"
    $env:PORT = $Port
    
    python app.py
}

function Start-Production {
    param([int]$Port)
    
    Write-Header
    Write-Info "Starting server in PRODUCTION mode..."
    Write-Info "Port: $Port"
    Write-Info "Workers: 4"
    Write-Info "Timeout: 120s"
    Write-Info ""
    Write-Host "Server will start at http://0.0.0.0:$Port" -ForegroundColor Green
    Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
    Write-Host ""
    
    $env:FLASK_ENV = "production"
    $env:FLASK_DEBUG = "False"
    $env:PORT = $Port
    $env:PYTHONUNBUFFERED = "1"
    
    gunicorn --workers 4 --bind 0.0.0.0:$Port 'backend.app:app' --timeout 120
}

function Run-Tests {
    Write-Header
    Write-Info "Running test suite..."
    Write-Host ""
    
    python test_system.py "http://localhost:8080"
}

# Main execution
if ($Help) {
    Show-Help
    exit
}

Write-Header

# Check and setup
if (-not (Check-Requirements)) {
    Write-Error "Requirements check failed"
    exit 1
}

Activate-Environment

if (-not (Install-Dependencies)) {
    Write-Error "Dependency installation failed"
    exit 1
}

if (-not (Setup-Environment)) {
    Write-Error "Environment setup failed"
    exit 1
}

if (-not (Initialize-Database)) {
    Write-Error "Database initialization failed"
    exit 1
}

Write-Host ""

# Run tests or start server
if ($Test) {
    Run-Tests
} else {
    if ($Mode -eq "prod") {
        Start-Production -Port $Port
    } else {
        Start-Development -Port $Port
    }
}
