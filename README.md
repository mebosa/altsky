# AltSky - SkyBlock Profile Viewer

AltSky is a SkyBlock profile viewer with a Django/DRF backend, a Go stats
calculator, and a SvelteKit frontend.

## Stack
- Backend: Django + DRF + Celery
- Stats calculator: Go service in `backend/statscalc`
- Frontend: SvelteKit (Vite)
- Infra: Docker Compose (Postgres, Nginx, Cloudflared)

## Quick start (local, Windows)
1. Copy `.env.example` to `.env` and set `HYPIXEL_API_KEY`.
2. Run `setup.ps1` (installs deps, migrates DB, collects static assets).
3. Run `run_server.ps1`.

The default local endpoints are:
- Backend: `http://localhost:8000`
- Frontend preview: `http://localhost:4173`

Manual run (no PowerShell scripts):
```powershell
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000

cd ../frontend
npm install
npm run dev
```

Optional stats calculator:
```powershell
cd backend/statscalc
go run ./cmd/statscalc -data ./data -addr :8082
```

## Docker
```powershell
Copy-Item .env.docker .env
docker-compose up -d
docker-compose exec backend python manage.py migrate
```

Service endpoints:
- Nginx: `http://localhost:8080`
- API: `http://localhost:8000/api/`
- Admin: `http://localhost:8000/admin/`

## Configuration
Main env vars (see `.env.example` and `.env.docker`):
- `DJANGO_SECRET`
- `HYPIXEL_API_KEY`
- `DB_PASSWORD` (Docker)
- `VITE_API_BASE` (frontend API base URL)

## Docs
- `DOCKER_GUIDE_KO.md`
- `DEPLOYMENT_GUIDE_KO.md`
- `STATS_EXPANSION_SUMMARY.md`
- `ops/cloudflare/README.md` (Cloudflare Tunnel for external testing)

## License
MIT
