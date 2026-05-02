# Repository Triage

| File | Decision | Reason | Migration Note |
|---|---|---|---|
| `code_analyzer/__init__.py` | REWRITE | Current exports point at the legacy `CodeAnalyzer` package shape and do not match the new `code_council` package boundary. | Replace with a new `apps/api/code_council/__init__.py` that exports the new backend surface. |
| `code_analyzer/main.py` | PORT | This is the core LLM orchestration logic and still contains the main provider wrappers, prompt flow, parsing, and fix generation hooks. | Move to `apps/api/code_council/analyzer.py`, rename `CodeAnalyzer` to `Analyzer`, remove `langchain`, `chroma`, Anthropic, and legacy feature coupling. |
| `code_analyzer/models.py` | PORT | Pure dataclasses with minimal coupling and directly useful for backend responses. | Move to `apps/api/code_council/models.py` and extend with API-facing payload models if needed. |
| `code_analyzer/config.py` | DELETE | The current config is tied to removed providers and the legacy monolith shape. | Replace with explicit environment/config logic in the new backend package. |
| `code_analyzer/prompts.py` | PORT | Prompt intent survives, but templates should be slimmed to simple string constants/f-strings. | Move to `apps/api/code_council/prompts.py` and inline the old LangChain template usage. |
| `code_analyzer/utils.py` | PORT | `timer_decorator` and `parse_llm_response` are reusable backend utilities. | Move to `apps/api/code_council/utils.py` with light cleanup. |
| `code_analyzer/evaluator.py` | ARCHIVE | Historical model comparison logic is not needed in the stateless product runtime. | Preserve in `legacy/` as evidence of earlier experimentation. |
| `code_analyzer/fix_suggestions.py` | PORT | Fix generation and diffing are still part of the new thorough mode experience. | Move to `apps/api/code_council/fixes.py` and keep only runtime-relevant pieces. |
| `code_analyzer/language_detector.py` | PORT | Language detection is still part of the new product and is lightweight to keep. | Move to `apps/api/code_council/language.py`. |
| `code_analyzer/framework_analyzer.py` | ARCHIVE | Framework-specific heuristics are explicitly out of scope for Code Council. | Preserve under `legacy/` only. |
| `code_analyzer/security_analyzer.py` | PORT | Regex + AST scanning remains part of the kept feature set and backs `/scan`. | Move to `apps/api/code_council/scanners/security.py`. |
| `code_analyzer/performance_analyzer.py` | PORT | Pattern-based performance scanning remains in scope for `/scan`. | Move to `apps/api/code_council/scanners/performance.py` and keep the lightweight report path. |
| `code_analyzer/cloud_analyzer.py` | ARCHIVE | Cloud analyzer is explicitly cut from the refreshed scope. | Preserve under `legacy/` only. |
| `code_analyzer/container_analyzer.py` | ARCHIVE | Container/Kubernetes analysis is explicitly cut from the refreshed scope. | Preserve under `legacy/` only. |
| `code_analyzer/multimodal_analyzer.py` | PORT | Vision analysis survives, but provider support and implementation details must change. | Move to `apps/api/code_council/multimodal.py` and refit around Gemini/Kimi-compatible flows. |
| `code_analyzer/advanced_analyzer.py` | REWRITE | This file is the legacy monolith coupling old UI, analyzers, and dead providers. The concept survives as a service layer only. | Replace with thin orchestration inside FastAPI and the new `Analyzer`. |
| `code_analyzer/dashboard.py` | ARCHIVE | SQLite dashboard persistence is cut from the new product. | Preserve under `legacy/` as prior portfolio work. |
| `code_analyzer/github_analyzer.py` | PORT | The URL parsing and fetch logic is reusable even though the HTTP endpoint is currently cut. | Move to `apps/api/code_council/github.py` but keep it out of the active API surface for now. |
| `code_analyzer/ci_cd_integration.py` | ARCHIVE | CI/CD quality gate tooling is outside the new runtime scope. | Preserve under `legacy/` only. |
| `code_analyzer/openai_fix.py` | DELETE | This is a workaround for old OpenAI proxy issues and relies on removed LangChain imports. | Replace with direct OpenAI-compatible SDK/httpx usage inside the new analyzer layer. |
| `code_analyzer/web/__init__.py` | DELETE | The legacy web package exists only to support Streamlit. | Remove once the new frontend is in `apps/web`. |
| `code_analyzer/web/app.py` | REWRITE | The old Streamlit Matrix UI is the exact surface being replaced. | Discard runtime role and rebuild the product in Next.js. |
| `code_analyzer/web/templates/dashboard.html` | ARCHIVE | Historical dashboard template is useful as portfolio evidence, not runtime code. | Preserve in `legacy/`. |
| `README.md` | REWRITE | The product framing, architecture, and run instructions are all changing. | Rewrite for Code Council after the new stack is in place. |
| `STREAMLIT_README.md` | ARCHIVE | Documentation for the removed Streamlit UI should not remain part of the live product narrative. | Move under `legacy/` or keep as archived historical docs. |
| `requirements.txt` | DELETE | Dependency set is oversized and tied to removed Streamlit/LangChain/Chroma runtime. | Replace with `apps/api/pyproject.toml` and frontend package manifests. |
| `requirements_force.txt` | DELETE | Legacy dependency override file is not compatible with the target stack. | Remove. |
| `Dockerfile` | DELETE | The current container build is for the legacy app and deployment path. | Replace with backend-specific Dockerfile in `apps/api/`, and later a root `docker-compose.yml`. |
| `render.yaml` | DELETE | Render deployment is not part of the target deployment plan. | Remove in favor of Railway + Vercel. |
| `quality_metrics.db` | ARCHIVE | Historical SQLite data is not used by the new stateless runtime. | Preserve as legacy evidence if desired, but do not wire it up. |
| `chroma_db/` | DELETE | ChromaDB is explicitly cut from the product. | Remove entirely. |
| `.gitignore` | REWRITE | The ignore rules currently target the old Python-only layout. | Replace with monorepo-friendly Python + Node + editor ignores. |
| `.dockerignore` | REWRITE | The ignore list should align with the new monorepo containers. | Refresh once backend/frontend containers exist. |
| `.python-version` | PORT | Python version intent still matters for the backend. | Keep or relocate as part of backend tooling. |
| `.env` | PORT | Environment variables still drive provider availability. | Retain locally, but add `apps/api/.env.example` and avoid committing secrets. |
| `projectstate.md` | ARCHIVE | Useful historical context, but describes the pre-migration app. | Preserve as a legacy design record. |
| `code_council_plan.md` | PORT | This is the authoritative migration plan for the repo. | Keep at the root or reference from docs during the transition. |
| `site color.jpg` | ARCHIVE | Static design asset is not part of the runtime. | Preserve if needed for branding references. |
| `test_code_image.jpg` | ARCHIVE | Useful sample asset for multimodal testing, not runtime code. | Preserve for manual testing. |
| `.venv/` | DELETE | Broken local virtual environment, not project source. | Remove locally and recreate a clean env outside version control if needed. |
| `testenv/` | DELETE | Incomplete/broken Python environment, not project source. | Remove locally. |

## Summary

- **PORT** preserves the reusable analyzer primitives.
- **REWRITE** replaces the old UI and orchestration layers with the Code Council runtime.
- **ARCHIVE** keeps earlier experiments as portfolio evidence without coupling them to the new product.
- **DELETE** removes dead dependencies, dead runtime paths, and broken environment artifacts.
