# AltSky 초기 설정 및 의존성 설치
# 관리자 권한으로 실행해야 합니다!

$projectRoot = "c:\altskydev\altsky"

Write-Host "================================" -ForegroundColor Cyan
Write-Host "AltSky 초기 설정" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# 1. 백엔드 패키지 설치
Write-Host "`n[1/4] 백엔드 패키지 설치 중..." -ForegroundColor Yellow
$backendPath = "$projectRoot\backend"
Set-Location $backendPath
pip install -r requirements.txt
pip install gunicorn python-dotenv certbot

Write-Host "[✓] 백엔드 패키지 설치 완료" -ForegroundColor Green

# 2. Statscalc 의존성 설치
Write-Host "`n[2/4] Statscalc 의존성 설치 중..." -ForegroundColor Yellow
$statscalcPath = "$projectRoot\backend\statscalc"
Set-Location $statscalcPath
go mod download
Write-Host "[✓] Statscalc 의존성 설치 완료" -ForegroundColor Green

# 3. 프론트엔드 패키지 설치 및 빌드
Write-Host "`n[3/4] 프론트엔드 설정 중..." -ForegroundColor Yellow
$frontendPath = "$projectRoot\frontend"
Set-Location $frontendPath
npm install

Write-Host "[✓] 프론트엔드 패키지 설치 완료" -ForegroundColor Green

# 4. 데이터베이스 마이그레이션
Write-Host "`n[4/4] 데이터베이스 마이그레이션..." -ForegroundColor Yellow
Set-Location $backendPath
python manage.py migrate
python manage.py collectstatic --noinput

Write-Host "[✓] 데이터베이스 마이그레이션 완료" -ForegroundColor Green

Write-Host "`n================================" -ForegroundColor Green
Write-Host "✓ 초기 설정 완료!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host "`n다음 명령어로 서버를 시작하세요:" -ForegroundColor Cyan
Write-Host "powershell -ExecutionPolicy Bypass -File run_server.ps1" -ForegroundColor White
