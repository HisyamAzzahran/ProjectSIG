$ErrorActionPreference = 'Stop'
$projectPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $projectPython)) {
    throw 'Buat .venv dan instal requirements.txt terlebih dahulu.'
}
Push-Location -LiteralPath $PSScriptRoot
try { & $projectPython -m src.serve_scbd @args }
finally { Pop-Location }
