$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot

if (-not (Test-Path ".venv")) {
  python -m venv .venv
}

$pythonExe = Join-Path $PSScriptRoot ".venv\\Scripts\\python.exe"
$pipExe = Join-Path $PSScriptRoot ".venv\\Scripts\\pip.exe"

& $pythonExe -m pip install --upgrade pip setuptools wheel

$reqInstalled = $true
try {
  & $pipExe install -r requirements.txt
} catch {
  $reqInstalled = $false
}

if (-not $reqInstalled) {
  $fallbacks = @(
    "Flask",
    "numpy",
    "opencv-python",
    "Pillow",
    "cryptography",
    "transformers"
  )
  foreach ($pkg in $fallbacks) {
    try { & $pipExe install $pkg } catch {}
  }
  try { & $pipExe install torch torchvision } catch {}
}

try { & $pythonExe validate_system.py } catch {}

Start-Process "http://127.0.0.1:5000"
& $pythonExe app.py
