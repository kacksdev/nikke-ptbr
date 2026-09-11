[CmdletBinding()]
param(
    [string]$Configuration = 'Release',
    [string]$PythonCommand = 'python'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$project = Join-Path $repositoryRoot 'installer\NIKKEPTBR.Installer\NIKKEPTBR.Installer.csproj'
$previousPythonUtf8 = [Environment]::GetEnvironmentVariable('PYTHONUTF8', 'Process')

Push-Location $repositoryRoot
try {
    $env:PYTHONUTF8 = '1'
    & $PythonCommand 'tools\audit_public_repository.py'
    if ($LASTEXITCODE -ne 0) {
        throw 'A auditoria do conteúdo público falhou.'
    }

    & $PythonCommand -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) {
        throw 'Os testes do núcleo transacional falharam.'
    }

    & dotnet build $project -c $Configuration --nologo
    if ($LASTEXITCODE -ne 0) {
        throw 'A compilação da interface do instalador falhou.'
    }

    $builtExecutable = Join-Path $repositoryRoot "installer\NIKKEPTBR.Installer\bin\$Configuration\net472\NIKKEPTBR.exe"
    if (-not (Test-Path -LiteralPath $builtExecutable -PathType Leaf)) {
        throw 'A compilação terminou sem produzir o executável esperado.'
    }

    Write-Host 'Conteúdo público, testes e interface aprovados.'
}
finally {
    [Environment]::SetEnvironmentVariable('PYTHONUTF8', $previousPythonUtf8, 'Process')
    Pop-Location
}
