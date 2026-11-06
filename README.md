# Frownloader

The repository keeps the frontend and backend in separate top-level folders:

```text
frontend/   Next.js website
backend/    FastAPI service and video processing
```

## Frontend

```powershell
cd frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Install JavaScript
dependencies with `npm install` from `frontend/` if needed. Configure the API
address in `frontend/.env.local` using `frontend/.env.example` as a guide.

### Cloudflare Pages

The frontend is configured for a static export. In Cloudflare Pages, keep the
repository root as the project root, set the build command to
`cd frontend && npm ci && npm run build`, and use `frontend/out` as the build
output directory. The root `wrangler.jsonc` records this Pages output path.
Set `NEXT_PUBLIC_API_URL` to the deployed backend URL in the build environment,
and configure the backend's `FRONTEND_ORIGINS` to include the deployed
frontend origin. For a direct upload from the repository root, first build the
frontend, then run `npx wrangler pages deploy frontend/out`.

## Backend

See [backend/README.md](backend/README.md) for Python setup, FFmpeg
installation, environment settings, and API verification commands. In brief:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn frownloader_api.main:app --reload --host 127.0.0.1 --port 8000 --env-file .env
```

The backend requires Python and FFmpeg on `PATH`. Only download content you
are authorized to save; platform availability and formats vary by source.
