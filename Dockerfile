# 멀티 스테이지 빌드

# Stage 1: 프론트엔드 서버 (SvelteKit preview)
FROM node:22-alpine AS frontend-server
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

EXPOSE 4173
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "4173"]

# Stage 2: 백엔드
FROM python:3.11-slim AS backend

WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 패키지 설치
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# 백엔드 코드 복사
COPY backend/ ./backend/

WORKDIR /app/backend

# 환경 변수
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings

# Gunicorn 실행
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"]

# Stage 3: Nginx에 정적 파일 포함
FROM nginx:alpine AS frontend-nginx
COPY --from=frontend-builder /app/frontend/build /usr/share/nginx/html
# nginx.conf는 compose에서 마운트해 덮어씁니다.


