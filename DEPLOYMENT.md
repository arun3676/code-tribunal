# Deployment

Code Tribunal deploys as two services:

- **Frontend:** `apps/web` on Vercel — landing at `/`, live Tribunal demo at `/tribunal`, Code Council editor at `/council`
- **Backend API:** `apps/api` on Railway

The frontend calls `/health`, `/tribunal/fixtures`, `/tribunal/run`, plus Solo/Council routes.

## 1. Deploy API on Railway

Railway service root directory:

```text
apps/api
```

Start command (default from Dockerfile):

```bash
uvicorn code_council.server:app --host 0.0.0.0 --port $PORT --workers 1
```

### Railway environment variables

```env
GROQ_API_KEY=
CEREBRAS_API_KEY=
GEMINI_API_KEY=
TRIBUNAL_LLM_PROVIDERS=groq,cerebras,gemini

# Optional per-provider model overrides
# (defaults: llama-3.3-70b-versatile / zai-glm-4.7 / gemini-3.5-flash)
# GROQ_MODEL=
# CEREBRAS_MODEL=
# GEMINI_MODEL=

# Waitlist invitations — landing-page signups land in this Resend audience.
# Until both are set, POST /waitlist logs registrations instead.
RESEND_API_KEY=
RESEND_AUDIENCE_ID=

DEEPSEEK_API_KEY=
MERCURY_API_KEY=
KIMI_API_KEY=

COORDINATION_BACKEND=band
BAND_ENABLED=true
BAND_STRICT=true
BAND_API_KEY=
BAND_BASE_URL=https://app.band.ai/api/v1
BAND_CLERK_ID=
BAND_ADVOCATE_ID=
BAND_SURVEYOR_ID=
BAND_GHOST_ID=
BAND_DRIFT_ID=
BAND_WARDEN_ID=
BAND_ARBITER_ID=

# Optional — messages appear from each agent identity
BAND_CLERK_API_KEY=
BAND_ADVOCATE_API_KEY=
BAND_SURVEYOR_API_KEY=
BAND_GHOST_API_KEY=
BAND_DRIFT_API_KEY=
BAND_WARDEN_API_KEY=
BAND_ARBITER_API_KEY=

ALLOWED_ORIGINS=https://YOUR-VERCEL-DOMAIN.vercel.app
ALLOWED_ORIGIN_REGEX=https://.*\.vercel\.app
```

### Pre-deploy smoke test (local)

```bash
python scripts/verify_all_keys.py
python scripts/verify_band_trial.py
```

### Post-deploy verify

```bash
curl https://YOUR-RAILWAY-API/health
curl https://YOUR-RAILWAY-API/tribunal/fixtures
curl -N -X POST https://YOUR-RAILWAY-API/tribunal/run \
  -H "Content-Type: application/json" \
  -d '{"fixture_id":"auth-login-001"}'
```

Confirm a new Band chat room appears at [app.band.ai](https://app.band.ai).

## 2. Deploy Web on Vercel

Vercel project root directory:

```text
apps/web
```

Environment variables:

```env
NEXT_PUBLIC_API_URL=https://YOUR-RAILWAY-API
NEXT_PUBLIC_SITE_URL=https://code-council.vercel.app
```

`NEXT_PUBLIC_SITE_URL` is the canonical production URL — it feeds the OG/social metadata, so
set it to your real domain if you deploy under a different one.

## 3. Connect CORS

After Vercel deploy, set Railway `ALLOWED_ORIGINS` to your production Vercel URL. Keep `ALLOWED_ORIGIN_REGEX` for preview deployments.

## 4. Production smoke test

Open `https://YOUR-VERCEL-APP/tribunal`:

- [ ] Landing page loads at `/`; Code Council editor loads at `/council`
- [ ] Page loads (no `BACKEND_OFFLINE`)
- [ ] Load **auth-login-001** → **Convene Tribunal**
- [ ] GHOST flags R3 (rate limiting missing)
- [ ] DRIFT flags auth middleware change
- [ ] WARDEN recruited
- [ ] Verdict: DOES_NOT_CONFORM, BLOCK
- [ ] Band room created (side-by-side check)
- [ ] No CORS or mixed-content errors
- [ ] Service worker picked up the deploy — the PWA (`public/sw.js`) is network-first, but
      offline fallbacks come from a versioned cache (`CACHE_NAME`, e.g. `tribunal-v2`). If a
      deploy changes precached shells, bump `CACHE_NAME` so `activate` purges the old cache;
      then reload the page twice and confirm no stale UI
