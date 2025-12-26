# AltSky 서버 실행 스크립트
# 관리자 권한으로 실행해야 합니다!

$projectRoot = "c:\altskydev\altsky"

Write-Host "================================" -ForegroundColor Cyan
Write-Host "AltSky 서버 시작" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# 1. Statscalc 실행
Write-Host "`n[1/3] Statscalc 서비스 시작 중..." -ForegroundColor Yellow
$statscalcPath = "$projectRoot\backend\statscalc"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$statscalcPath'; go run ./cmd/statscalc" -WindowStyle Normal

# 2. 백엔드 실행
Write-Host "[2/3] 백엔드 시작 중..." -ForegroundColor Yellow
$backendPath = "$projectRoot\backend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backendPath'; python manage.py runserver 0.0.0.0:8000" -WindowStyle Normal

# 3. 프론트엔드 실행
Write-Host "[3/3] 프론트엔드 시작 중..." -ForegroundColor Yellow
Start-Sleep -Seconds 2
$frontendPath = "$projectRoot\frontend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontendPath'; npm run preview" -WindowStyle Normal

Write-Host "`n================================" -ForegroundColor Green
Write-Host "✓ 서버가 시작되었습니다!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host "백엔드: http://localhost:8000" -ForegroundColor Cyan
Write-Host "프론트엔드: http://localhost:4173" -ForegroundColor Cyan
Write-Host "`n도메인으로 접속: http://altsky.info" -ForegroundColor Cyan
