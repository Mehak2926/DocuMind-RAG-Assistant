$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$pythonArgs = @()
if (Get-Command py -ErrorAction SilentlyContinue) {
    foreach ($version in @("-3.11", "-3.12", "-3.10")) {
        & py $version --version *> $null
        if ($LASTEXITCODE -eq 0) {
            $python = "py"
            $pythonArgs = @($version)
            break
        }
    }
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $python = "python"
} else {
    throw 'Python was not found. Install Python 3.11 or 3.12 and enable "Add Python to PATH".'
}

if (-not $python) {
    throw 'Python 3.10, 3.11, or 3.12 was not found. Install Python 3.11 and enable "Add Python to PATH".'
}

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Creating virtual environment..."
    & $python @pythonArgs -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw "Failed to create the virtual environment." }
}

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r requirements.txt

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env. Add your GROQ_API_KEY before asking questions."
}

& $venvPython -m streamlit run app.py
