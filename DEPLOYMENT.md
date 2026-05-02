# Deployment

Code Council deploys as two services:

- Frontend: `apps/web` on Vercel.
- Backend API: `apps/api` on Railway.

The frontend needs the backend. It calls `/health`, `/models`, `/analyze`, `/council`, `/scan`, and `/multimodal`.

## 1. Deploy API on Railway

Create a Railway service from this repository with root directory:

```text
apps/api
```

Railway should use the Dockerfile in `apps/api`. The container listens on `0.0.0.0:$PORT`; Railway injects `PORT` automatically.

Set these Railway environment variables:

```env
GEMINI_API_KEY=...
DEEPSEEK_API_KEY=...
MERCURY_API_KEY=...
Kimi_API_KEY=...
ALLOWED_ORIGINS=https://your-vercel-app.vercel.app
ALLOWED_ORIGIN_REGEX=https://.*\.vercel\.app
```

After Railway deploys, verify:

```bash
curl https://your-railway-domain.up.railway.app/health
curl https://your-railway-domain.up.railway.app/models
```

## 2. Deploy Web on Vercel

Create a Vercel project from this repository with root directory:

```text
apps/web
```

Set this Vercel environment variable before building:

```env
NEXT_PUBLIC_API_URL=https://your-railway-domain.up.railway.app
```

Use the default Next.js output. The app includes `apps/web/vercel.json` with the install and build commands.

## 3. Connect CORS

Once the final Vercel production URL is known, update Railway:

```env
ALLOWED_ORIGINS=https://your-vercel-app.vercel.app,https://your-custom-domain.com
```

Keep `ALLOWED_ORIGIN_REGEX=https://.*\.vercel\.app` if you want Vercel preview deployments to call the Railway API.

## 4. Smoke Test

Open the deployed Vercel URL and confirm:

- Header does not show `BACKEND_OFFLINE`.
- All four model indicators are visible.
- Solo analysis returns a score, bugs, suggestions, and raw stream.
- Council analysis completes with all four models and no `MODEL UNRESPONSIVE` cards.
