# Code Council
 
 Code Council — see how frontier models reason about your code.

## Hero Screenshot

Add a dark Council View screenshot here once the new frontend is running locally or deployed.

## What this is

Code Council is a multi-model code analysis sandbox. Instead of one AI verdict, it lets you stream several model opinions over the same code and compare where they agree, disagree, or miss things entirely.

## Why this exists

Most code-review AI products optimize for a single fast answer during PR time. That is useful, but it hides one of the most interesting parts of working with models: they often notice different risks, emphasize different tradeoffs, and disagree in ways that are actually informative.

Code Council turns that disagreement into the product. The point is not to auto-merge fixes or replace engineering judgment. The point is to give you a place to inspect how multiple frontier models think about the same snippet, with streamed output, consensus signals, static scans, and multimodal input.

## Stack

- Next.js 15
- FastAPI
- Railway
- Vercel
- Gemini
- DeepSeek
- Mercury
- Kimi

## Run locally

```bash
git clone <repository-url>
cd llm-code-analyzer
docker compose up
```

Create a root `.env` file before starting local services.

Required variables:

```env
GEMINI_API_KEY=
DEEPSEEK_API_KEY=
MERCURY_API_KEY=
Kimi_API_KEY=
ALLOWED_ORIGINS=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Deploy

Deploy this as two services:

- `apps/api` -> Railway
- `apps/web` -> Vercel

The Vercel frontend needs the Railway backend URL in `NEXT_PUBLIC_API_URL`. The Railway backend needs the Vercel frontend origin in `ALLOWED_ORIGINS`; use `ALLOWED_ORIGIN_REGEX=https://.*\.vercel\.app` if you want Vercel preview deployments to work.

See [`DEPLOYMENT.md`](DEPLOYMENT.md) for the full checklist.

## Architecture

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## What's in `/legacy`

The `legacy/` directory preserves earlier iterations of the project: the original Streamlit UI, dashboard work, CI/CD tooling, and other analyzer experiments that helped shape the current product. They are intentionally kept as portfolio evidence, but they are not part of the active runtime.

## License

MIT
