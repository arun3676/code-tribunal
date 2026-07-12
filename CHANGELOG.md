# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-07-11

Release-ready cut of the `code-tribunal` package. Install from the repo until the
PyPI release lands:
`uvx --from "git+https://github.com/arun3676/code-tribunal.git#subdirectory=apps/api" tribunal --help`

### Added
- **CLI** — `tribunal verify` (full court, exit 0/1 for CI), `tribunal ghost`
  (fast omission pre-check), `tribunal drift` (fast scope-drift pre-check),
  `tribunal init <openclaw|hermes|claude|codex|cursor>` (emits MCP wiring
  config), and `tribunal doctor` (BYO-key health check per provider).
- **MCP server** — `tribunal-mcp` (stdio) exposing `verify_intent_conformance`,
  `ghost_check`, and `drift_check`; installable clone-free via
  `uvx --from code-tribunal tribunal-mcp`.
- **BYOK multi-provider reasoning** — Groq → Cerebras → Gemini fallback chain
  (`TRIBUNAL_LLM_PROVIDERS`), per-provider model overrides, deterministic
  fallback when no keys are configured.
- Animated marketing landing with self-contained waitlist (Resend-backed) and
  courtroom "summons" welcome email.
- MCP e2e test suite over the SDK's in-memory transport; `py.typed` marker;
  runtime `code_council.__version__`.

### Changed
- Zero-key deterministic engine made honest: free-form tickets extract
  requirements; unverifiable requirements yield CONDITION instead of a silent
  pass; blockers always force BLOCK.
- Default models refreshed: Groq `llama-3.3-70b-versatile`, Cerebras
  `zai-glm-4.7`, Gemini `gemini-3.5-flash`.
- FastAPI startup migrated to a lifespan handler; API version now tracks the
  package version.

### Removed
- Legacy hackathon docs and the AI/ML API + Featherless provider dependencies.

## [0.2.0] - 2026-06-22

Post-hackathon relaunch groundwork: three decoupled layers (reasoning /
coordination / scoring), `CoordinationBackend` seam with Band adapter and
no-op backend, deterministic trust scoring with traceability ledger.

## [0.1.0] - 2026-06-18

Hackathon submission: Code Council multi-model editor and the first Tribunal
War Room demo.

[0.3.0]: https://github.com/arun3676/code-tribunal/releases/tag/v0.3.0
