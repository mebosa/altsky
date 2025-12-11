# AltSky Docker 배포 가이드

## 🐳 Docker 설치

### Windows 11에서 Docker Desktop 설치
1. https://www.docker.com/products/docker-desktop 에서 다운로드
2. 설치 후 PowerShell 재시작
3. 확인:
```powershell
docker --version
docker-compose --version
```

---

## 🚀 배포 (3단계)

### 1️⃣ 환경 변수 설정
```powershell
# .env.docker 파일을 .env로 복사
Copy-Item .env.docker .env

# 또는 PowerShell에서 직접 설정
$env:DJANGO_SECRET="your-secure-secret-key-here"
$env:HYPIXEL_API_KEY="44906786-2f9e-4a1f-a15e-85f88d65f54a"
$env:DB_PASSWORD="your-secure-password"
```

### 2️⃣ Docker 이미지 빌드 및 실행
```powershell
cd c:\altskydev\altsky

# 이미지 빌드 + 컨테이너 시작 (백그라운드)
docker-compose up -d

# 또는 로그를 보면서 시작
docker-compose up
```

### 3️⃣ 데이터베이스 마이그레이션 (처음 한 번만)
```powershell
# 백엔드 컨테이너에서 마이그레이션 실행
docker-compose exec backend python manage.py migrate

# 관리자 계정 생성 (필요시)
docker-compose exec backend python manage.py createsuperuser
```

---

## 📍 접속 방법

```
브라우저: http://localhost
API: http://localhost:8000/api/
관리자: http://localhost:8000/admin/
```

또는 도메인으로:
```
http://altsky.info
```

---

## 🛑 컨테이너 관리

### 현재 실행 중인 컨테이너 보기
```powershell
docker-compose ps
```

### 로그 확인
```powershell
# 모든 서비스
docker-compose logs -f

# 특정 서비스
docker-compose logs -f backend
docker-compose logs -f nginx
docker-compose logs -f db
```

### 서비스 재시작
```powershell
docker-compose restart backend
```

### 전부 중지
```powershell
docker-compose down

# 데이터도 삭제 (주의!)
docker-compose down -v
```

---

## 🔐 프로덕션 설정 (HTTPS)

### Let's Encrypt 인증서 발급 (Linux에서)
```bash
sudo certbot certonly --standalone -d altsky.info -d www.altsky.info
```

### Windows에서 발급 (WSL 이용)
```powershell
# WSL에서
wsl
sudo certbot certonly --standalone -d altsky.info -d www.altsky.info
```

### 인증서 복사
```powershell
# WSL에서 생성된 인증서를 Windows로 복사
mkdir certs
cp /mnt/c/path/to/certs/fullchain.pem certs/cert.pem
cp /mnt/c/path/to/certs/privkey.pem certs/key.pem
```

### nginx.conf에서 HTTPS 활성화
`nginx.conf`의 주석 처리된 HTTPS 블록 활성화 후:
```powershell
docker-compose restart nginx
```

---

## 🐛 문제 해결

### 포트 이미 사용 중
```powershell
# 포트 80 사용 중인 프로세스 찾기
netstat -ano | findstr :80

# 또는 docker-compose에서 포트 변경
# docker-compose.yml에서 "80:80" → "8080:80" 등으로 변경
```

### 이미지 재빌드 (코드 변경 후)
```powershell
docker-compose build --no-cache
docker-compose up -d
```

### 데이터베이스 리셋
```powershell
docker-compose down -v
docker-compose up -d
docker-compose exec backend python manage.py migrate
```

### 특정 서비스만 재시작
```powershell
docker-compose up -d --no-deps --build backend
```

---

## 📊 모니터링

### 실시간 리소스 사용량
```powershell
docker stats
```

### 컨테이너 상세 정보
```powershell
docker-compose ps -a
docker inspect altsky-api
```

---

## 🔄 백업 및 복원

### 데이터베이스 백업
```powershell
docker-compose exec db pg_dump -U altsky altsky > backup.sql
```

### 데이터베이스 복원
```powershell
docker-compose exec -T db psql -U altsky altsky < backup.sql
```

---

## 📝 주의사항

1. **DJANGO_SECRET**: 프로덕션에서는 반드시 안전한 무작위 문자열로 변경
2. **DB_PASSWORD**: 강력한 암호로 변경
3. **방화벽**: 포트 80, 443 외부 접근 허용 필요
4. **백업**: 정기적으로 데이터베이스 백업
5. **모니터링**: `docker-compose logs`로 에러 확인

---

## ✅ 배포 체크리스트

- [ ] Docker Desktop 설치
- [ ] `.env` 파일 설정
- [ ] `docker-compose up -d` 실행
- [ ] `docker-compose exec backend python manage.py migrate` 실행
- [ ] 브라우저에서 http://localhost 접속 확인
- [ ] 가비아에서 DNS A 레코드 설정 (118.217.102.48)
- [ ] http://altsky.info 접속 확인
- [ ] HTTPS 인증서 설정 (선택사항)

---

**완료!** 🎉 이제 Docker로 배포되었습니다.
문제 발생 시 `docker-compose logs`에서 에러를 확인해주세요!
