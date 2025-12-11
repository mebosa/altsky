# AltSky 서버 배포 가이드 (Windows 11)

## 🚀 빠른 시작 (3단계)

### 1️⃣ 초기 설정 (처음 한 번만)
```powershell
# PowerShell을 관리자 권한으로 실행
cd c:\altskydev\altsky
powershell -ExecutionPolicy Bypass -File setup.ps1
```

**이 명령어가 하는 일:**
- ✅ 백엔드 Python 패키지 설치
- ✅ 프론트엔드 npm 패키지 설치  
- ✅ 데이터베이스 마이그레이션
- ✅ 정적 파일 수집

---

### 2️⃣ 서버 시작 (매번)
```powershell
cd c:\altskydev\altsky
powershell -ExecutionPolicy Bypass -File run_server.ps1
```

**이 명령어가 하는 일:**
- ✅ 백엔드 실행 (포트 8000)
- ✅ 프론트엔드 실행 (포트 4173)
- ✅ 두 개의 터미널 자동 생성

---

### 3️⃣ 브라우저에서 접속
```
http://localhost:4173    (로컬 프론트엔드)
http://localhost:8000    (로컬 백엔드 API)
http://altsky.info       (도메인으로 접속)
```

---

## 🔧 상세 설명

### 백엔드 (Django)
- **위치**: `c:\altskydev\altsky\backend`
- **포트**: 8000
- **명령어**: `python manage.py runserver 0.0.0.0:8000`

### 프론트엔드 (SvelteKit)
- **위치**: `c:\altskydev\altsky\frontend`
- **포트**: 4173
- **명령어**: `npm run preview`

### API 연결
- 프론트엔드는 자동으로 `http://localhost:8000`의 백엔드와 통신
- (설정: `frontend/.env.local`)

---

## 📍 가비아 DNS 설정 (중요!)

1. **가비아 관리 페이지** 접속
2. **DNS 관리** → `altsky.info` 선택
3. **A 레코드** 추가:
   ```
   호스트: @ (또는 altsky.info)
   타입: A
   값: [노트북의 공인 IP]
   TTL: 300
   ```

4. **www 서브도메인** (선택사항):
   ```
   호스트: www
   타입: CNAME
   값: altsky.info
   TTL: 300
   ```

---

## 🔐 설정 파일

### 백엔드 환경 변수 (`backend/.env`)
```
DEBUG=0                                           # 프로덕션 모드
ALLOWED_HOSTS=altsky.info,www.altsky.info,...    # 허용된 도메인
CSRF_TRUSTED_ORIGINS=https://altsky.info,...     # CSRF 보호
SECURE_SSL_REDIRECT=1                            # HTTPS 강제
```

### 프론트엔드 환경 변수 (`frontend/.env.local`)
```
VITE_API_BASE=http://localhost:8000              # 백엔드 API 주소
```

---

## ⚠️ 주의사항

1. **노트북이 켜져있어야 함**: 서버를 실행하는 동안만 접속 가능
2. **방화벽 설정**: Windows 방화벽에서 포트 8000, 4173 허용 필요
3. **공인 IP 변경**: ISP에서 IP를 변경하면 가비아 DNS 업데이트 필요
4. **인증서**: HTTPS 사용하려면 Let's Encrypt 설정 필요

---

## 🐛 문제 해결

### 포트 이미 사용 중
```powershell
# 포트 8000 사용 중인 프로세스 찾기
netstat -ano | findstr :8000

# 프로세스 종료 (PID는 위에서 확인)
taskkill /PID [PID] /F
```

### npm 명령어 없음
```powershell
# Node.js/npm 설치 확인
node --version
npm --version

# 설치되지 않았으면
# https://nodejs.org/ 에서 설치
```

### 데이터베이스 오류
```powershell
cd backend
python manage.py migrate --run-syncdb
```

---

## 📞 추가 지원 필요시
문제 발생 시 터미널 에러 메시지를 복사해서 알려주세요!
