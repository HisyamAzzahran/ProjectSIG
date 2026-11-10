$ErrorActionPreference = 'Stop'
$projectDirectory = $PSScriptRoot
$projectPython = Join-Path $projectDirectory '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $projectPython)) {
    throw 'Create .venv and install requirements.txt as documented in README.md first.'
}
& $projectPython (Join-Path $projectDirectory 'knime\setup\launch_knime.py') @args
exit $LASTEXITCODE
