# Frontend — PromptSentry SOC Console (v1)

Next.js app that polls `GET /admin/logs` every 5s. Does **not** talk to Postgres.

## Run (API must already be up)

```bash
cd promptsentry
docker compose up -d

cd frontend
cp .env.local.example .env.local   # if needed
npm install
npm run dev
```

Open http://localhost:3000 — paste your `PROMPTSENTRY_API_KEYS` value in the top bar.

## Env

- `NEXT_PUBLIC_API_BASE_URL` — default `http://localhost:8000`
