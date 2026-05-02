# LLM Code Analyzer - Project State (Single Source of Truth)

> **Purpose:** This document serves as the complete contextual reference for the LLM Code Analyzer project. Feed this file to any LLM to understand every module, dependency, flow, and design decision without needing to read individual source files.

---

## 1. Project Overview

**LLM Code Analyzer** is an AI-powered code analysis tool with a Streamlit web interface. It analyzes source code using multiple Large Language Models (LLMs), detects bugs, suggests improvements, and supports multimodal analysis (code + images). It also includes specialized analyzers for security, performance, frameworks, cloud platforms, and containers.

### Core Capabilities
- **Multi-Model Support:** OpenAI GPT, Anthropic Claude, DeepSeek, Mercury, Google Gemini
- **Code Analysis:** Quality scoring, bug detection, improvement suggestions, documentation generation
- **Multimodal Analysis:** Analyze code screenshots, diagrams, UI mockups via vision-capable LLMs
- **Specialized Analyzers:** Security, Performance, Framework-specific, Cloud, Container/Kubernetes
- **GitHub Integration:** Analyze code from GitHub URLs (single files or repositories)
- **CI/CD Integration:** Quality gates for pull requests and commits
- **Code Quality Dashboard:** SQLite-backed trend tracking with matplotlib charts
- **RAG Integration:** ChromaDB for context-aware suggestions
- **Chat with Code:** Conversational Q&A about analyzed code

---

## 2. Project Structure

```
llm-code-analyzer/
├── code_analyzer/                  # Main Python package
│   ├── __init__.py                 # Package init
│   ├── main.py                     # Core CodeAnalyzer class (primary LLM orchestrator)
│   ├── models.py                   # Data models (dataclasses)
│   ├── config.py                   # Default configuration
│   ├── prompts.py                  # LLM prompt templates
│   ├── utils.py                    # Utility functions (timer, response parser)
│   ├── evaluator.py                # Model performance evaluator
│   ├── fix_suggestions.py          # AI-powered code fix suggestion generator
│   ├── language_detector.py        # Language/framework/build-tool detector
│   ├── framework_analyzer.py       # React, Django, Spring framework-specific analysis
│   ├── security_analyzer.py        # Security vulnerability scanner (patterns + AST)
│   ├── performance_analyzer.py     # Performance bottleneck detector + profiler
│   ├── cloud_analyzer.py           # AWS, Azure, GCP cloud pattern analysis
│   ├── container_analyzer.py       # Dockerfile and Kubernetes YAML analyzer
│   ├── multimodal_analyzer.py      # Image analysis via GPT-4V, Claude, Gemini Vision
│   ├── advanced_analyzer.py        # Integrates all analyzers + model switching + chat
│   ├── dashboard.py                # SQLite-backed code quality dashboard + charts
│   ├── github_analyzer.py          # GitHub URL/file/repo fetcher and analyzer
│   ├── ci_cd_integration.py        # CI/CD quality gates with CLI interface
│   ├── openai_fix.py               # OpenAI client proxy-bypass wrapper
│   └── web/                        # Streamlit web application
│       ├── __init__.py             # Web module init
│       ├── app.py                  # Main Streamlit UI (Matrix cyberpunk theme)
│       └── templates/
│           └── dashboard.html      # Standalone HTML dashboard template
├── chroma_db/                      # ChromaDB persistent vector store
├── requirements.txt                # Python dependencies
├── requirements_force.txt          # Forced dependency versions (fallback)
├── .env                            # API keys (DO NOT COMMIT)
├── .gitignore                      # Git ignore rules
├── Dockerfile                      # Docker container config
├── render.yaml                     # Render.com deployment config
├── README.md                       # General project README
├── STREAMLIT_README.md             # Streamlit-specific documentation
└── projectstate.md               # THIS FILE
```

---

## 3. File-by-File Deep Dive

### `code_analyzer/models.py`
**Purpose:** Pure data models. No logic.

| Class | Fields |
|-------|--------|
| `CodeAnalysisResult` | `code_quality_score: float`, `potential_bugs: List[str]`, `improvement_suggestions: List[str]`, `documentation: str`, `model_name: str`, `execution_time: float`, `fix_suggestions: Optional[List[Any]]` |
| `ModelEvaluationResult` | `model_name: str`, `average_quality_score: float`, `average_execution_time: float`, `success_rate: float`, `analysis_samples: List[CodeAnalysisResult]` |

---

### `code_analyzer/config.py`
**Purpose:** Default configuration dictionary.

```python
DEFAULT_CONFIG = {
    "models": {
        "deepseek": {"name": "deepseek-chat", "temperature": 0.1, "max_tokens": 2000},
        "claude": {"name": "claude-3-haiku-20240307", "temperature": 0.1, "max_tokens": 2000},
        "mercury": {"name": "mercury-coder", "temperature": 0.1, "max_tokens": 2000}
    },
    "analysis": {"min_quality_score": 0, "max_quality_score": 100, "timeout": 30}
}
```

---

### `code_analyzer/prompts.py`
**Purpose:** LLM prompt templates.

- `CODE_ANALYSIS_PROMPT`: Asks for JSON with `code_quality_score`, `potential_bugs`, `improvement_suggestions`
- `DOCUMENTATION_PROMPT`: Asks for comprehensive markdown documentation

---

### `code_analyzer/utils.py`
**Purpose:** Helper utilities.

| Function | Behavior |
|----------|----------|
| `timer_decorator` | Wraps functions to measure and attach `execution_time` to result objects |
| `parse_llm_response(response: str)` | Extracts JSON from LLM response. Falls back to line-by-line heuristic parsing if JSON fails. Recognizes keywords like "quality score", "bug", "suggestion", "documentation" |

---

### `code_analyzer/evaluator.py`
**Purpose:** Tracks and compares model performance over time.

| Class | Key Methods |
|-------|-------------|
| `ModelEvaluator` | `add_result(result)`, `get_evaluation(model_name)`, `compare_models()` |

Computes average quality score, average execution time, and success rate from stored `CodeAnalysisResult`s.

---

### `code_analyzer/main.py` (CORE ORCHESTRATOR)
**Purpose:** Primary `CodeAnalyzer` class. Initializes LLM clients, runs code analysis, handles retries, parallel calls, and mode switching.

**Key Classes:**
- `DeepSeekWrapper`: Wraps DeepSeek API using OpenAI SDK (`base_url="https://api.deepseek.com"`)
- `MercuryWrapper`: Wraps Mercury API using OpenAI SDK (`base_url="https://api.inceptionlabs.ai/v1"`)
- `AnthropicWrapper` (inner class in `__init__`): Wraps direct `anthropic.Anthropic` client

**`CodeAnalyzer.__init__(self, config, mock=False)`:**
1. Loads config from `DEFAULT_CONFIG` or provided dict
2. Initializes ephemeral ChromaDB client (cleans `chroma_data` dir)
3. Conditionally initializes `FrameworkAnalyzer`, `CloudAnalyzer`, `ContainerAnalyzer`
4. Validates API keys from env: `DEEPSEEK_API_KEY`, `ANTHROPIC_API_KEY`, `MERCURY_API_KEY`
5. Registers models in `self.models` dict (keys: "deepseek", "claude", "mercury")
6. Initializes `FixSuggestionGenerator` with first available LLM client
7. Initializes `LanguageDetector`
8. Sets up LangChain `PromptTemplate`s for analysis and documentation

**`CodeAnalyzer.analyze_code(self, code, model, file_path, language, mode)`:**
- **Modes:**
  - `"quick"`: Strict short prompts (max 2 bugs, 2 suggestions, 600 tokens). Claude/Mercury get special "no code/markdown" instructions. No fix suggestions.
  - `"thorough"`: Full prompts (2000 tokens), generates fix suggestions, fills empty fields with defaults.
- **Flow:**
  1. Validates input and model availability
  2. Detects language via `LanguageDetector` (defaults to Python)
  3. Builds model-specific prompts with language context
  4. **Parallel LLM calls** via `ThreadPoolExecutor` (analysis + documentation simultaneously)
  5. **Retry logic** with exponential backoff (3 attempts)
  6. Parses responses via `parse_llm_response`
  7. **Post-processing for Claude/Mercury quick mode:** Detects if response is code/markdown and replaces with fallback message
  8. In thorough mode, generates fix suggestions via `FixSuggestionGenerator`
  9. Returns `CodeAnalysisResult`

**`CodeAnalyzer.analyze_with_all_models(self, code, mode)`:** Runs `analyze_code` against every registered model and returns a dict of results.

---

### `code_analyzer/fix_suggestions.py`
**Purpose:** Generates actionable code fix suggestions with before/after diffs.

**Key Dataclasses:**
- `CodeFix`: `issue_type`, `severity`, `description`, `line_number`, `original_code`, `fixed_code`, `explanation`, `confidence`, `tags`, `related_links`
- `FixSuggestion`: Extends `CodeFix` with `diff`, `can_auto_apply`, `plain_explanation`, `learn_more_link`

**`FixSuggestionGenerator`:**
- **Pattern-based fixes** (fallback): Predefined regex replacements for `unused_variables`, `magic_numbers`, `long_functions`, `sql_injection`, `xss`, `hardcoded_secrets`, `nested_loops`, etc.
- **AI-powered fixes** (primary): Sends an LLM prompt requesting JSON with `title`, `explanation`, `original_code`, `fixed_code`, `confidence`, `tags`, `related_links`, `can_auto_apply`
- `_generate_diff()`: Simple line-by-line diff (`- old`, `+ new`)
- `apply_fix()`: String replacement of original with fixed code
- `get_fix_summary()`: Aggregates counts by severity and type

---

### `code_analyzer/language_detector.py`
**Purpose:** Detects programming languages, frameworks, build tools, and dependencies from code or project directories.

**Key Dataclasses:**
- `LanguageInfo`: `name`, `version`, `confidence`, `file_extension`, `shebang`
- `FrameworkInfo`: `name`, `version`, `confidence`, `type`
- `DetectionResult`: `language`, `frameworks`, `build_tools`, `dependencies`, `confidence`

**`LanguageDetector`:**
- **Language detection** (12 languages supported): python, javascript, typescript, java, cpp, csharp, go, rust, php, ruby, swift, kotlin, scala
- **Detection order:** File extension → Shebang → Keyword matching
- **Framework detection** (per language): Django/Flask/FastAPI/pandas/TensorFlow/PyTorch (Python), React/Vue/Angular/Express (JS), Spring/Android (Java), Qt/Boost (C++), ASP.NET/EF (C#)
- **Build tool detection:** requirements.txt, package.json, pom.xml, go.mod, Cargo.toml, etc.
- **Dependency extraction:** Parses requirements.txt, setup.py, package.json, pom.xml

---

### `code_analyzer/framework_analyzer.py`
**Purpose:** Detects framework-specific anti-patterns.

**Supported frameworks:** React, Django, Spring

**Issues detected:**
- React: Missing `useEffect` for API calls, missing `key` prop in lists
- Django: Raw SQL in views, missing CSRF protection
- Spring: Field injection (should use constructor injection), missing `@Transactional`

**`FrameworkAnalyzer.analyze_code(file_path, code)` → returns dict with `framework`, `issues`, `total_issues`**

---

### `code_analyzer/security_analyzer.py`
**Purpose:** Security vulnerability scanner using regex patterns + Python AST.

**Key Dataclasses:**
- `SecurityVulnerability`: `vulnerability_type`, `severity`, `description`, `line_number`, `code_snippet`, `file_path`, `cwe_id`, `remediation`, `confidence`
- `SecurityReport`: `vulnerabilities`, `summary`, `risk_score`, `recommendations`, `scan_timestamp`

**Detection methods:**
1. **Pattern-based:** SQL injection, XSS, command injection, path traversal, hardcoded secrets, weak crypto (MD5/SHA1), insecure random, debug code
2. **AST-based (Python only):** `eval()`, `exec()`, `pickle.loads()`
3. **AI-based:** Placeholder for LLM-driven analysis

**Risk score calculation:** Weighted by severity (critical=10, high=7, medium=4, low=1) normalized to 0-100.

**Reports:** JSON, HTML, or text format.

---

### `code_analyzer/performance_analyzer.py`
**Purpose:** Detects performance anti-patterns and can profile Python code.

**Key Dataclasses:**
- `PerformanceIssue`: `issue_type`, `severity`, `description`, `line_number`, `code_snippet`, `file_path`, `impact`, `suggestion`, `complexity`, `estimated_improvement`, `ai_optimization`
- `PerformanceReport`: `issues`, `summary`, `overall_score`, `recommendations`, `complexity_analysis`, `scan_timestamp`, `ai_insights`, `optimization_examples`

**Anti-patterns detected:**
- Nested loops (O(n²))
- Inefficient list operations
- String concatenation in loops
- Unnecessary computations in loops
- Memory inefficient operations
- Inefficient data structures (list lookups instead of sets/dicts)
- Recursive functions without memoization

**Features:**
- AST-based complexity analysis (cyclomatic complexity, nested loop counting)
- **`profile_function(func, *args, **kwargs)`**: Uses `cProfile` + `pstats` to profile execution
- **`benchmark_alternatives(code_versions)`**: Compares multiple function implementations
- **`profile_memory_usage(func)`**: Uses `psutil` to measure memory delta
- **AI insights:** Optional LLM-generated optimization examples

---

### `code_analyzer/cloud_analyzer.py`
**Purpose:** Detects cloud platform anti-patterns.

**Platforms:** AWS, Azure, GCP

**Issues detected:**
- AWS: Hardcoded credentials, missing error handling on boto3 calls, public S3 buckets
- Azure: Hardcoded connection strings, missing retry policies
- GCP: Hardcoded project IDs, missing authentication

**`CloudAnalyzer.analyze_code(file_path, code)` → returns dict with `platform`, `issues`, `total_issues`**

---

### `code_analyzer/container_analyzer.py`
**Purpose:** Dockerfile and Kubernetes YAML analysis.

**Key Dataclass:**
- `ContainerIssue`: `issue_type`, `severity`, `message`, `line_number`, `suggestion`, `code_example`, `config_type`

**Dockerfile checks:**
- Running as root (`USER root`)
- Missing `HEALTHCHECK`
- Using `:latest` tag
- Missing multi-stage builds

**Kubernetes checks:**
- Missing resource limits
- Missing security context
- Using `:latest` image tag
- Missing liveness probes

---

### `code_analyzer/multimodal_analyzer.py`
**Purpose:** Analyzes images (code screenshots, diagrams, UI mockups) using vision-capable LLMs.

**Supported models:**
- Google Gemini Pro Vision (`gemini-pro-vision`)
- Anthropic Claude 3.5 Sonnet (`claude-3-5-sonnet-20241022`)
- OpenAI GPT-4V (client initialized but not actively used in current methods)

**`MultiModalAnalyzer.analyze_image(image_file, prompt, model)` → returns dict:**
- `analysis`: Full text response
- `code_extracted`: Code blocks extracted from response
- `suggestions`: Bullet-point suggestions extracted from response
- `model`: Which model was used

**Image preprocessing:**
- Converts to RGB
- Resizes if dimension > 2048px
- Saves as JPEG quality 95
- Base64 encodes for API transmission

---

### `code_analyzer/advanced_analyzer.py`
**Purpose:** Integrates ALL analyzers. Main entry point for the Streamlit app.

**Key Dataclasses:**
- `AdvancedAnalysisResult`: `code_analysis`, `security_report`, `performance_report`, `multimodal_analysis`, `analysis_timestamp`, `analysis_duration`, `features_used`
- `AnalysisConfig`: `enable_rag`, `enable_security`, `enable_performance`, `enable_multimodal`, `codebase_path`, `openai_api_key`, `max_rag_results`, `security_scan_level`, `performance_analysis_level`

**`AdvancedCodeAnalyzer`:**
- **Model switching:** `model_switcher(model)` returns the appropriate LLM client from `self.llm_clients`
- **Chat with code:** `chat_with_code(code, chat_history, user_question)` — sends full conversation + code context to LLM for Q&A
- **`analyze_code_advanced(code, language, model)`**: Runs basic LLM analysis + optionally security/performance/multimodal (note: security/performance/multimodal integration is currently stubbed/commented in the implementation)
- **`analyze_image(image_file, prompt, model)`**: Delegates to `MultiModalAnalyzer`
- **`analyze_image_all(image_file, prompt)`**: Runs all available vision models
- **LLM client initialization:** `_initialize_llm_clients()` creates wrappers for OpenAI, Claude, Gemini, DeepSeek, Mercury — all using direct API clients to avoid LangChain proxy issues

---

### `code_analyzer/dashboard.py`
**Purpose:** Code quality trend dashboard with SQLite persistence and matplotlib charts.

**Key Dataclasses:**
- `QualityMetric`: `timestamp`, `file_path`, `language`, `quality_score`, `model_name`, `execution_time`, `bug_count`, `suggestion_count`, `complexity_score`, `performance_score`, `security_score`, `maintainability_score`
- `TrendData`: `metric_name`, `values`, `timestamps`, `trend_direction`, `trend_strength`, `average_value`, `min_value`, `max_value`
- `DashboardReport`: `overall_quality_trend`, `language_breakdown`, `model_performance`, `top_issues`, `improvement_areas`, `recommendations`, `generated_at`, `time_period`, `total_analyses`

**`CodeQualityDashboard`:**
- **Database:** SQLite (`quality_metrics.db` by default)
- **Schema:** `quality_metrics` table with indexed columns: `timestamp`, `language`, `model_name`, `file_path`
- **`record_analysis(analysis_result, file_path, language, model_name)`**: Stores analysis metrics
- **`get_metrics(days, language_filter, model_filter)`**: Retrieves metrics with optional filters
- **`calculate_trends(metrics)`**: Uses numpy linear regression to determine trend direction (`improving`/`declining`/`stable`) and strength (-1 to 1)
- **`generate_dashboard_report(days)`**: Comprehensive report with language breakdown, model performance comparison, top issue files, improvement areas
- **`generate_charts(days)`**: Returns base64-encoded PNG charts:
  - Quality score trend (line chart with trend line)
  - Language breakdown (pie chart)
  - Model performance (dual bar chart: quality + execution time)
  - Bug count trend (line chart)
- Uses `dark_background` matplotlib style with `husl` seaborn palette

---

### `code_analyzer/github_analyzer.py`
**Purpose:** Fetch and analyze code from GitHub URLs.

**`GitHubAnalyzer`:**
- **URL parsing:** Supports `github.com/owner/repo/blob/branch/path`, `github.com/owner/repo/blob/path` (assumes main), `github.com/owner/repo` (repo root)
- **`get_file_content(owner, repo, branch, file_path)`**: Fetches raw content from `raw.githubusercontent.com`
- **`get_repo_files(owner, repo, branch, max_files)`**: Uses GitHub Trees API to list code files
- **`analyze_github_link(github_url, prompt, model)`**:
  - Single file → fetches + analyzes via `AdvancedCodeAnalyzer`
  - Repository → fetches first 3 code files, combines, analyzes as one

---

### `code_analyzer/ci_cd_integration.py`
**Purpose:** Automated code quality gates for CI/CD pipelines. Has CLI interface.

**Key Dataclasses:**
- `QualityGate`: `min_quality_score` (70), `max_security_risk` (30), `max_performance_issues` (5), `max_critical_issues` (0), `max_high_issues` (2), `require_documentation`, `require_tests`, `allowed_languages`
- `PipelineResult`: `passed`, `quality_score`, `security_risk`, `performance_score`, `issues_found`, `critical_issues`, `high_issues`, `recommendations`, `report_path`, `failed_gates`

**`CICDIntegrator`:**
- **`analyze_pull_request(base_branch, head_branch, repo_path, output_format)`**: Gets changed files via `git diff`, analyzes each, checks quality gates
- **`analyze_commit(commit_hash, repo_path, output_format)`**: Gets files in commit via `git show`, analyzes, checks gates
- **Quality gates checked:**
  1. Average quality score >= threshold
  2. Max security risk <= threshold
  3. Total issues <= threshold
  4. Critical issues == 0
  5. High issues <= threshold
- **Reports:** JSON, HTML, or text format saved to `ci_analysis_report_{timestamp}`
- **CLI:** `python -m code_analyzer.ci_cd_integration --mode pr|commit --base-branch main --output-format json|html|text`
- **Exit code:** 0 if passed, 1 if failed (for CI integration)

---

### `code_analyzer/openai_fix.py`
**Purpose:** Standalone OpenAI client initializer that bypasses proxy issues.

- `initialize_openai_client()`: Creates `openai.OpenAI(api_key=...)` directly, tests with a simple completion, returns `OpenAIWrapper` with `.invoke()` method matching LangChain interface

---

### `code_analyzer/web/app.py` (STREAMLIT UI)
**Purpose:** Main web application. Matrix cyberpunk theme.

**Page config:** `page_title="🤖 LLM Code Analyzer"`, `layout="wide"`

**Theme features:**
- Black background (`#000`) with green text (`#00ff41`)
- Matrix rain effect via JavaScript canvas (injected via `st.components.v1.html`)
- Glowing borders, cyber buttons with hover sweep animation
- Orbitron font header

**Tabs:**
1. **"Code Analysis"**
   - Sidebar: Model selector (OpenAI, Anthropic, DeepSeek, Mercury, Gemini)
   - Main: Large code textarea (300px), "Analyze" button
   - API key status indicator (red/green)
   - Results displayed in 4 subtabs: Summary, Issues, Suggestions, Metrics
   - **Chat with Code:** Persistent chat interface below results. Sends `chat_with_code()` calls to `AdvancedCodeAnalyzer`. Clear chat button.

2. **"Multimodal Analysis"**
   - Image uploader (png, jpg, jpeg)
   - Optional prompt text input
   - 3 buttons: "Analyze with Gemini Vision", "Analyze with Claude", "Analyze with All Models"

**Result display functions:**
- `display_analysis_results(result, title)`: Shows summary, bugs (red errors), suggestions (blue info), metrics
- `display_fix_suggestions(suggestions)`: Expanders per suggestion
- `display_security_results(security_result)`: Security-specific output
- `display_multimodal_results(result, model_name)`: Image analysis output

---

### `code_analyzer/web/templates/dashboard.html`
**Purpose:** Standalone responsive HTML dashboard (not actively served by Streamlit app, but available as a template).

- Cyberpunk gradient theme with `#39ff14` (green) and `#00fff7` (cyan)
- Stats cards grid: Total Analyses, Avg Quality Score, Bugs Found, Suggestions
- Chart placeholders (intended for AJAX-loaded data)
- Recent activity list
- jQuery-based data loading from `/stats` and `/recent_activity` endpoints
- Fully responsive: mobile-first, tablet (768px+), desktop (1024px+)

---

## 4. Dependencies (`requirements.txt`)

| Package | Version | Purpose |
|---------|---------|---------|
| streamlit | 1.36.0 | Web UI framework |
| langchain | 0.2.6 | LLM orchestration (used for prompts/templates) |
| langchain-core | 0.2.10 | Core LangChain abstractions |
| langchain-openai | 0.1.9 | OpenAI LangChain integration |
| langchain-anthropic | 0.1.12 | Anthropic LangChain integration |
| langchain-community | 0.2.6 | Community LangChain extensions |
| langchain-google-genai | 1.0.6 | Google Gemini LangChain integration |
| chromadb | 0.4.24 | Vector database for RAG |
| openai | >=1.0.0 | OpenAI API client (also used for DeepSeek/Mercury) |
| anthropic | 0.29.0 | Anthropic API client |
| google-generativeai | latest | Google Generative AI SDK |
| python-dotenv | 1.0.1 | .env file loading |
| gitpython | 3.1.43 | Git operations |
| pillow | 10.4.0 | Image processing for multimodal |
| sentence-transformers | latest | Text embeddings for RAG |
| tiktoken | latest | Token counting |
| torch | latest | PyTorch (for embeddings) |
| transformers | latest | Hugging Face transformers |
| scikit-learn | latest | ML utilities |
| scipy | latest | Scientific computing |
| numpy | latest | Numerical computing |
| pandas | latest | Data manipulation (dashboard) |
| plotly | latest | Interactive charts |
| matplotlib | latest | Static charts (dashboard) |
| mercury-sdk | latest | Mercury API SDK |
| requests | latest | HTTP requests (GitHub, APIs) |
| websockets | latest | WebSocket support |
| streamlit-option-menu | latest | UI component |
| httpcore | <1.0.0 | HTTP core (version pinned for compatibility) |
| protobuf | latest | Protocol buffers |
| blinker | 1.8.2 | Signal support (Flask/Streamlit dependency) |

**Note:** `yaml` (PyYAML) is also used in `container_analyzer.py` but not explicitly in requirements.txt — it likely comes as a transitive dependency.

---

## 5. Environment Variables (`.env`)

All loaded via `python-dotenv` at module import time.

| Variable | Provider | Required For |
|----------|----------|-------------|
| `OPENAI_API_KEY` | OpenAI | GPT models, multimodal base client |
| `ANTHROPIC_API_KEY` | Anthropic | Claude models |
| `DEEPSEEK_API_KEY` | DeepSeek | DeepSeek-chat model |
| `MERCURY_API_KEY` | Inception Labs | Mercury-coder model |
| `GEMINI_API_KEY` | Google | Gemini Pro Vision |
| `GITHUB_TOKEN` | GitHub | GitHub repo analysis (optional, for higher rate limits) |

---

## 6. Architecture & Data Flow

### Standard Code Analysis Flow
```
User Input (code)
    ↓
[Streamlit app.py] ←→ [AdvancedCodeAnalyzer]
    ↓
[CodeAnalyzer.main.py] — initializes LLM wrappers
    ↓
Language Detection ← [LanguageDetector]
    ↓
Parallel LLM Calls (analysis + documentation)
    ↓
Response Parsing ← [utils.parse_llm_response]
    ↓
Fix Suggestions ← [FixSuggestionGenerator] (thorough mode only)
    ↓
CodeAnalysisResult
    ↓
Display in Streamlit tabs
```

### Multimodal Analysis Flow
```
User uploads image
    ↓
[app.py] → [AdvancedCodeAnalyzer.analyze_image()]
    ↓
[MultiModalAnalyzer]
    ↓
Image Preprocessing (resize, RGB, JPEG, base64)
    ↓
Vision LLM API (Gemini / Claude / OpenAI)
    ↓
Extract code blocks + suggestions
    ↓
Display results
```

### CI/CD Flow
```
Git PR / Commit triggered
    ↓
[ci_cd_integration.py CICDIntegrator]
    ↓
git diff → changed files
    ↓
[AdvancedCodeAnalyzer] per file
    ↓
Quality Gate Checks
    ↓
Report generated (JSON/HTML/Text)
    ↓
Exit 0 (pass) or 1 (fail)
```

### Dashboard Flow
```
Analysis completed
    ↓
[dashboard.py record_analysis()]
    ↓
SQLite INSERT into quality_metrics
    ↓
[dashboard.py generate_dashboard_report()]
    ↓
Trend calculation (numpy polyfit)
    ↓
Chart generation (matplotlib → base64 PNG)
    ↓
Display / Export
```

---

## 7. Deployment

### Local Development
```bash
pip install -r requirements.txt
streamlit run code_analyzer/web/app.py
# Opens on http://localhost:8501
```

### Docker
```bash
docker build -t llm-code-analyzer .
docker run -p 8501:8501 -e OPENAI_API_KEY=... -e ANTHROPIC_API_KEY=... llm-code-analyzer
```
**Dockerfile:** Python 3.11-slim base, installs git + ffmpeg, pip installs requirements, exposes 8501, runs Streamlit on `0.0.0.0`

### Render.com
- `render.yaml` defines web service
- Python 3.11, auto-detected
- Build: `pip install -r requirements.txt`
- Start: `streamlit run code_analyzer/web/app.py --server.port $PORT --server.address 0.0.0.0`
- Environment variables must be set in Render dashboard

---

## 8. Key Design Decisions

1. **Direct API Clients over LangChain:** Due to proxy issues, the project uses direct `openai.OpenAI()`, `anthropic.Anthropic()`, and custom wrappers for DeepSeek/Mercury instead of relying on LangChain chat models. LangChain is still used for `PromptTemplate` and message abstractions.

2. **Graceful Degradation:** Every specialized analyzer is imported inside `try/except` blocks. If a module fails to import, the system logs a warning and continues without that feature.

3. **Ephemeral ChromaDB:** The vector store is ephemeral (in-memory) and the `chroma_data` directory is cleaned on init. This avoids persistent state issues but means RAG context is per-session.

4. **Quick vs Thorough Modes:** Quick mode uses constrained prompts and lower token limits for speed. Thorough mode uses full prompts, generates fix suggestions, and ensures no empty fields.

5. **Model-Specific Prompt Engineering:** Claude and Mercury receive explicit "do NOT return code/markdown" instructions in quick mode because they tend to return verbose code blocks otherwise.

6. **Parallel LLM Calls:** Analysis and documentation prompts are sent simultaneously via `ThreadPoolExecutor` to reduce latency.

7. **Exponential Backoff:** LLM calls retry up to 3 times with `sleep(2^attempt)` between attempts.

8. **SQLite for Dashboard:** Simple file-based persistence for quality metrics. No external database required.

9. **Base64 Charts:** matplotlib charts are rendered to memory buffers and returned as base64 strings for easy embedding in web UIs.

10. **Unified Wrapper Interface:** All LLM clients (OpenAI, Claude, DeepSeek, Mercury) implement an `.invoke(prompt)` method returning an object with `.content` attribute, making them interchangeable.

---

## 9. Testing & Troubleshooting

### Mock Mode
`CodeAnalyzer(mock=True)` initializes with a mock LLM that returns "Mock response: Analyzed". Useful for testing UI without API keys.

### Common Issues
- **Import Errors:** Install all requirements: `pip install -r requirements.txt`
- **Missing API Keys:** Ensure `.env` file exists in project root
- **Proxy Errors:** The project intentionally bypasses LangChain proxies via direct clients
- **Port Conflicts:** `streamlit run code_analyzer/web/app.py --server.port <your_port>`

---

## 10. Extension Points

To add a new LLM provider:
1. Create a wrapper class with `__init__(api_key, model_name, temperature)` and `.invoke(prompt)` method
2. Add to `CodeAnalyzer.__init__()` model registration block
3. Add env var validation
4. Add to `AdvancedCodeAnalyzer._get_llm()` and `_initialize_llm_clients()`
5. Add to Streamlit sidebar in `app.py`

To add a new analyzer:
1. Create module with `analyze_code(file_path, code)` → return `{'type': '...', 'issues': [...], 'total_issues': N}`
2. Add conditional import in `main.py` / `advanced_analyzer.py`
3. Add UI display function in `app.py`

---

*Generated: May 2026 | Project: llm-code-analyzer | Context: Complete project reference for LLM consumption*
