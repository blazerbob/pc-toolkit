# Сборка PC Toolkit: сначала exe (PyInstaller), затем инсталлятор (Inno Setup).
# Запуск из корня репозитория:  powershell -ExecutionPolicy Bypass -File build\build.ps1

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

Write-Host "==> Сборка exe (PyInstaller)" -ForegroundColor Cyan
python -m PyInstaller --noconfirm --clean --onefile --windowed `
    --name "PC Toolkit" --paths src src/main.py

Write-Host "==> Сборка инсталлятора (Inno Setup)" -ForegroundColor Cyan
$iscc = if ($env:ISCC) { $env:ISCC } else { "D:\Inno Setup\ISCC.exe" }
if (-not (Test-Path $iscc)) {
    throw "Не найден ISCC.exe: $iscc (укажи путь в переменной ISCC)"
}
& $iscc "packaging\installer.iss"

Write-Host "==> Готово. Артефакты:" -ForegroundColor Green
Get-ChildItem "dist\installer" | Select-Object -ExpandProperty FullName