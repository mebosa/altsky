# Cloudflare Tunnel Setup

This folder shows how to expose the local SvelteKit frontend and Django API with [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/). Use it whenever external teammates need temporary access to your dev environment.

## 1. Prerequisites
- Cloudflare account with a zone (e.g. `example.com`).
- [`cloudflared`](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation) installed locally and logged in.
- Public DNS records (CNAME) created in Cloudflare for the hostnames you plan to share, e.g. `app.example.com` and `api.example.com`. Cloudflare will prompt for this during the tunnel setup.

## 2. Configure the tunnel
1. Create a tunnel if you do not already have one:
   ```bash
   cloudflared tunnel create altsky-dev
   ```
2. Copy `config.example.yml` to `config.yml` and update:
   - `tunnel` – replace with the tunnel id returned by Cloudflare.
   - `credentials-file` – absolute path to the JSON credentials file Cloudflare generated.
   - The `hostname` entries – set to the subdomains you added in Cloudflare DNS.
3. Register DNS routes (one time):
   ```bash
   cloudflared tunnel route dns altsky-dev app.example.com
   cloudflared tunnel route dns altsky-dev api.example.com
   ```

## 3. Run the local services
From separate terminals:
```bash
# Backend (Django)
cd backend
python manage.py runserver 0.0.0.0:8000

# Frontend (SvelteKit)
cd frontend
npm install
npm run dev
```

The Vite config is set to listen on all interfaces so Cloudflare can reach it. Populate `backend/.env` with the public hosts so Django accepts requests:
```bash
ALLOWED_HOSTS=localhost,127.0.0.1,app.example.com,api.example.com
CSRF_TRUSTED_ORIGINS=https://app.example.com,https://api.example.com
CORS_ALLOW_ALL_ORIGINS=0
CORS_ALLOWED_ORIGINS=https://app.example.com
```

Update `frontend/.env.local` (or environment variables on the host) to point to the public API origin:
```bash
VITE_API_BASE=https://api.example.com
```

## 4. Launch the tunnel
With the backend and frontend running, start the tunnel from the project root:
```bash
cloudflared tunnel --config ops/cloudflare/config.yml run altsky-dev
```

Cloudflare will proxy `app.example.com` to the SvelteKit dev server and `api.example.com` to Django. Share the hostnames with testers—when you stop the tunnel the hosts will no longer resolve.

## 5. Optional: background service
For repeated use you can run the tunnel as a service (systemd, Windows service, etc.). See the [Cloudflare docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/run-tunnel/as-a-service/) for platform-specific instructions.
