# copywrAIter — Development Tasks (PRD v1.5)

> Based on PRD.yaml v1.5 (Final) — "Autonomous Research & Copywriting Agent"
> Tech Stack: Python (FastAPI), SQLite, React/Next.js + Tailwind + shadcn/ui, APScheduler, Docker

---

## Phase 1: Foundation & Infrastructure

### 1.1 Database Migration: PostgreSQL → SQLite
- [ ] 1.1.1 Update `config.py` — change `DATABASE_URL` default to `sqlite:///./data/app.db`
- [ ] 1.1.2 Update `backend/app/database.py` — switch from sync SQLAlchemy to SQLite-compatible engine
  - Remove `asyncpg` dependency
  - Use `sqlite3` with `check_same_thread=False`
  - Keep `get_db()` generator pattern
- [ ] 1.1.3 Update `backend/app/models.py` — replace `postgresql.UUID` with SQLite-compatible UUID handling
  - Use `sqlalchemy.String` for UUID storage or `sqlalchemy_utils` UUID type
  - Remove `postgresql` dialect imports
- [ ] 1.1.4 Update all routers — replace sync `Session` with SQLite-compatible sessions
- [ ] 1.1.5 Update `requirements.txt` — remove `asyncpg`, `alembic` (optional), add `aiosqlite` if async needed
- [ ] 1.1.6 Test: All CRUD endpoints work with SQLite

### 1.2 Project Structure Reorganization
- [ ] 1.2.1 Create `backend/main.py` — FastAPI app entry point with CORS, router registration
- [ ] 1.2.2 Register all existing routers: agents, drafts, posts, trends, niches, vault, repliz, linkedin, profile, settings
- [ ] 1.2.3 Create `backend/.env.example` with SQLite-compatible defaults
- [ ] 1.2.4 Create `backend/Dockerfile` — multi-stage Python image
- [ ] 1.2.5 Create `docker-compose.yml` — backend + (optional) Redis for caching
- [ ] 1.2.6 Create `install.sh` — one-line bash installer (PRD: `curl -sSL ... | bash`)
  - Detects and installs Docker/Compose if missing
  - Auto-maps container to Port 8080 (configurable via .env)
  - Detects public VPS IP and provides setup link

### 1.3 Requirements & Dependencies
- [ ] 1.3.1 Finalize `backend/requirements.txt`:
  - `fastapi>=0.115.0`
  - `uvicorn[standard]>=0.32.0`
  - `sqlalchemy>=2.0.36`
  - `aiosqlite>=0.20.0` (async SQLite)
  - `pydantic>=2.10.0`
  - `pydantic-settings>=2.7.0`
  - `python-dotenv>=1.0.1`
  - `httpx>=0.28.0`
  - `python-multipart>=0.0.18`
  - `openai>=1.55.0`
  - `anthropic>=0.47.0`
  - `apscheduler>=3.10.0`
  - `crawl4ai` or `tavily-python` (research engine)
  - `langgraph` or `crewai` (agent framework)

---

## Phase 2: AI Intelligence Layer

### 2.1 Style Mimicry Engine
- [ ] 2.1.1 Create `backend/app/agents/style_analyzer.py`
  - Accepts existing content/posts as reference text
  - Analyzes: cadence (sentence length distribution), emoji usage frequency, vocabulary richness, tone markers
  - Returns structured style profile (JSON) for few-shot prompting
- [ ] 2.1.2 Add `style_profile` field to `ConfigStore` / `Setting` model
- [ ] 2.1.3 Integrate style profile into copywriter prompt generation
- [ ] 2.1.4 Create API endpoint: `POST /api/style/analyze` — accepts text, returns style profile
- [ ] 2.1.5 Create API endpoint: `GET /api/style/profile` — returns current style profile
- [ ] 2.1.6 Create API endpoint: `PUT /api/style/profile` — updates style profile

### 2.2 Localization Layer
- [ ] 2.2.1 Add `language` field to settings schema with options:
  - `"en"` — English
  - `"id_formal"` — Indonesian (Formal)
  - `"id_casual"` — Indonesian (Casual/Gaul)
  - `"custom"` — Custom (user defines)
- [ ] 2.2.2 Create `backend/app/services/localization.py`
  - Language-specific system prompt templates
  - Language-specific banned words/phrases lists
  - Custom language rules storage
- [ ] 2.2.3 Update `CopywriterAgent.generate()` to accept `language` parameter
- [ ] 2.2.4 Update `_build_warkop_system_prompt()` to be language-aware
- [ ] 2.2.5 Update `_build_warkop_user_prompt()` to include language-specific instructions

### 2.3 Research Engine (Crawl4AI / Tavily)
- [ ] 2.3.1 Create `backend/app/services/research_engine.py`
  - Abstract base class for research providers
  - Implement `TavilyResearchProvider` (if API key provided)
  - Implement `Crawl4AIResearchProvider` (free, no API key)
  - Fallback chain: Tavily → Crawl4AI → existing TrendHunter
- [ ] 2.3.2 Update `backend/services/trend_hunter.py`
  - Replace Google/Twitter placeholders with actual implementations
  - Integrate with new research engine
  - Add `score` field to Trend model (currently referenced in scheduler but missing)
- [ ] 2.3.3 Add `score` column to `Trend` model in `models.py`
- [ ] 2.3.4 Create API endpoint: `POST /api/research/search` — accepts topic, returns research results
- [ ] 2.3.5 Create API endpoint: `POST /api/research/refresh` — triggers fresh trend collection

### 2.4 Agent Framework Integration (LangGraph / CrewAI)
- [ ] 2.4.1 Create `backend/app/agents/workflow.py`
  - Define LangGraph state machine or CrewAI crew for: Research → Strategy → Generation pipeline
  - Stage 1: Research agent gathers real-time data
  - Stage 2: Strategy agent selects best framework + hook based on research
  - Stage 3: Copywriter agent generates content with style + language constraints
- [ ] 2.4.2 Update `backend/app/scheduler.py` to use new workflow instead of direct `copywriter_agent.generate()`
- [ ] 2.4.3 Add workflow execution logging for "Agent Thinking" log feature
- [ ] 2.4.4 Create API endpoint: `POST /api/workflow/run` — manual trigger of full workflow
- [ ] 2.4.5 Create API endpoint: `GET /api/workflow/status` — returns current workflow execution status

### 2.5 Native Knowledge Frameworks (Already Partially Done)
- [x] 2.5.1 Copywriting frameworks: AIDA, PAS, BAB, FAB, The 4 C's — **DONE** in `copywriter.py`
- [x] 2.5.2 Hook frameworks: Negative, Statistical, Curiosity, Authority, Question-Based — **DONE** in `copywriter.py`
- [ ] 2.5.3 Add auto-selection logic: AI picks best framework + hook based on topic + research data
- [ ] 2.5.4 Add framework/hook metadata to generated content output

---

## Phase 3: Functional Requirements — Content Identity Manager

### 3.1 Multi-Topic Selector
- [ ] 3.1.1 Create API endpoint: `GET /api/topics/trending` — returns trending niches from TrendHunter
- [ ] 3.1.2 Create API endpoint: `GET /api/topics/custom` — returns user's custom topics
- [ ] 3.1.3 Create API endpoint: `POST /api/topics/custom` — add custom topic
- [ ] 3.1.4 Create API endpoint: `DELETE /api/topics/custom/{id}` — remove custom topic
- [ ] 3.1.5 Update niche router to support topic selection workflow

### 3.2 Instruction Vault (Markdown Editor)
- [ ] 3.2.1 Extend `VaultItem` model with `content_type` field: `"skill"`, `"rule"`, `"persona"`
- [ ] 3.2.2 Create API endpoint: `GET /api/vault/categories` — returns grouped vault items by category
- [ ] 3.2.3 Create API endpoint: `POST /api/vault/bulk` — bulk create/update vault items
- [ ] 3.2.4 Add markdown validation/sanitization to vault content
- [ ] 3.2.5 Integrate vault content into copywriter prompt (already partially done via `_load_brand_voice()`)

### 3.3 Template Porter
- [ ] 3.3.1 Create `backend/app/services/template_exporter.py`
  - Generates `.md` template from current settings + vault + style profile
  - Template includes placeholders for Gemini/ChatGPT refinement
- [ ] 3.3.2 Create API endpoint: `GET /api/template/export` — downloads `.md` template file
- [ ] 3.3.3 Create API endpoint: `GET /api/template/preview` — returns template as JSON for preview

---

## Phase 4: Autonomous Workflow

### 4.1 Stage 1: Real-Time Research
- [ ] 4.1.1 Implement `ResearchAgent` in `backend/app/agents/researcher.py`
  - Takes topic/niche as input
  - Calls research engine (Tavily/Crawl4AI)
  - Returns structured research summary with key points, stats, quotes
- [ ] 4.1.2 Store research results in `Trend` model with `data` JSON field
- [ ] 4.1.3 Add research timestamp tracking

### 4.2 Stage 2: Strategy Selection
- [ ] 4.2.1 Implement `StrategyAgent` in `backend/app/agents/strategist.py`
  - Analyzes research data
  - Selects optimal framework (AIDA/PAS/BAB/FAB/4Cs) with reasoning
  - Selects optimal hook type with reasoning
  - Returns strategy decision as structured output
- [ ] 4.2.2 Store strategy decisions in content metadata

### 4.3 Stage 3: Content Generation with Variations
- [ ] 4.3.1 Update `CopywriterAgent.generate_with_frameworks()` to produce A/B variations
  - Generate 2 variations per slot (PRD: "A/B Drafts")
  - Each variation uses different framework/hook combination
  - Both variations respect style profile + instruction vault
- [ ] 4.3.2 Add `variation_id` and `parent_draft_id` to `Draft` model for grouping variations
- [ ] 4.3.3 Create API endpoint: `POST /api/generate/variations` — generates A/B drafts for a topic

### 4.4 Stage 4: Visual Content Calendar
- [ ] 4.4.1 Extend `Post` model with calendar fields:
  - `scheduled_at` (DateTime, nullable)
  - `calendar_slot_id` (String, for grouping)
- [ ] 4.4.2 Create API endpoint: `GET /api/calendar` — returns posts organized by date
- [ ] 4.4.3 Create API endpoint: `PUT /api/calendar/reorder` — drag-and-drop reorder (accepts new schedule)
- [ ] 4.4.4 Create API endpoint: `POST /api/calendar/slot` — create empty calendar slot
- [ ] 4.4.5 Create API endpoint: `DELETE /api/calendar/slot/{id}` — remove slot

### 4.5 Stage 5: Automated Posting via Repliz API
- [ ] 4.5.1 Create `backend/app/services/repliz_client.py`
  - HTTP client for Repliz API
  - Methods: `create_post()`, `schedule_post()`, `get_post_status()`, `test_connection()`
  - Error handling with retry logic
- [ ] 4.5.2 Add `repliz_api_key` and `repliz_base_url` to `ConfigStore` / `Setting` model
- [ ] 4.5.3 Create API endpoint: `POST /api/repliz/test` — tests Repliz API connection
- [ ] 4.5.4 Create API endpoint: `POST /api/repliz/publish/{post_id}` — publishes post via Repliz
- [ ] 4.5.5 Update scheduler to call Repliz at scheduled timestamps
- [ ] 4.5.6 Store `repliz_id` in `Post` model after successful publish (already exists)

---

## Phase 5: Monitoring & Alerts

### 5.1 Live "Agent Thinking" Log
- [ ] 5.1.1 Create `backend/app/services/agent_logger.py`
  - In-memory log buffer with WebSocket support
  - Logs each step: research started, framework selected, generation in progress, etc.
  - Structured log entries: `{timestamp, step, status, message, data}`
- [ ] 5.1.2 Create WebSocket endpoint: `WS /api/ws/agent-log` — real-time log stream
- [ ] 5.1.3 Create API endpoint: `GET /api/agent-log` — returns recent log entries (REST fallback)
- [ ] 5.1.4 Integrate agent logger into all agent workflows (research, strategy, copywriter)
- [ ] 5.1.5 Add log retention policy (keep last 1000 entries or 24 hours)

### 5.2 Telegram/Discord Webhook Notifications
- [ ] 5.2.1 Create `backend/app/services/notifier.py`
  - Abstract notification interface
  - Implement `TelegramWebhookNotifier`
  - Implement `DiscordWebhookNotifier`
  - Event types: `post_success`, `post_failed`, `generation_complete`, `error`
- [ ] 5.2.2 Add `notification_webhooks` JSON field to `Setting` model:
  ```json
  {
    "telegram": {"url": "...", "chat_id": "..."},
    "discord": {"url": "..."}
  }
  ```
- [ ] 5.2.3 Create API endpoint: `POST /api/notifications/test` — sends test notification
- [ ] 5.2.4 Integrate notifier into scheduler pipeline (on success/failure)
- [ ] 5.2.5 Integrate notifier into Repliz publish flow

---

## Phase 6: Setup Wizard UI (Backend Endpoints)

### 6.1 AI Configuration
- [ ] 6.1.1 Create API endpoint: `POST /api/config/ai` — saves AI provider config (base URL, API key)
- [ ] 6.1.2 Create API endpoint: `GET /api/config/ai` — returns current AI config (masked API key)
- [ ] 6.1.3 Create API endpoint: `POST /api/config/ai/models` — "Fetch Models" dynamic dropdown
  - Calls provider's model listing API
  - Returns list of available models
- [ ] 6.1.4 Create API endpoint: `POST /api/config/ai/test` — "Connection Test" button
  - Sends minimal prompt to verify API key + connectivity
  - Returns success/failure with response time

### 6.2 Distribution Configuration
- [ ] 6.2.1 Create API endpoint: `POST /api/config/distribution` — saves Repliz API key
- [ ] 6.2.2 Create API endpoint: `GET /api/config/distribution` — returns current distribution config
- [ ] 6.2.3 Create API endpoint: `POST /api/config/distribution/test` — "Test Post" button
  - Creates a draft test post via Repliz API
  - Verifies API permissions
  - Auto-deletes test post

### 6.3 Port & Deployment Config
- [ ] 6.3.1 Add `PORT` env variable to config (default: 8080 per PRD)
- [ ] 6.3.2 Add `PUBLIC_IP` detection in `install.sh`
- [ ] 6.3.3 Create API endpoint: `GET /api/config/system` — returns system info (port, IP, status)

---

## Phase 7: Frontend (React/Next.js + Tailwind + shadcn/ui)

### 7.1 Project Setup
- [ ] 7.1.1 Initialize Next.js project in `frontend/` directory
- [ ] 7.1.2 Configure Tailwind CSS
- [ ] 7.1.3 Install and configure shadcn/ui components
- [ ] 7.1.4 Set up API client (fetch wrapper with base URL from env)
- [ ] 7.1.5 Set up routing (Next.js App Router)
- [ ] 7.1.6 Create layout: sidebar navigation + main content area

### 7.2 Setup Wizard Page
- [ ] 7.2.1 Step 1: AI Configuration
  - Base URL input field
  - API Key input (masked)
  - "Fetch Models" dropdown (dynamic)
  - "Connection Test" button with loading state + result display
- [ ] 7.2.2 Step 2: Distribution Configuration
  - Repliz API Key input
  - "Test Post" button with loading state + result display
- [ ] 7.2.3 Step 3: Language Selection
  - Dropdown: English, Indonesian (Formal), Indonesian (Casual/Gaul), Custom
  - Custom language rules textarea (if "Custom" selected)
- [ ] 7.2.4 Step 4: Style Reference Input
  - Textarea for pasting existing content
  - "Analyze Style" button → shows style analysis results
- [ ] 7.2.5 Completion screen with dashboard link

### 7.3 Dashboard Page
- [ ] 7.3.1 Overview cards: Total Posts, Scheduled, Published, Drafts
- [ ] 7.3.2 Quick action buttons: Generate Content, View Calendar, Manage Topics
- [ ] 7.3.3 Recent activity feed (from agent log)
- [ ] 7.3.4 Next scheduled post countdown

### 7.4 Content Creation Page
- [ ] 7.4.1 Multi-Topic Selector
  - Dropdown with trending niches (fetched from API)
  - "Other" option → custom topic text input
  - Multi-select support
- [ ] 7.4.2 Instruction Vault Editor
  - Markdown editor (e.g., `@uiw/react-md-editor` or similar)
  - Tabs: Skills, Rules, General Persona
  - Save/preview functionality
- [ ] 7.4.3 Generation Controls
  - Framework selector (auto or manual)
  - Hook type selector (auto or manual)
  - Language selector
  - "Generate" button with loading state
- [ ] 7.4.4 Results Display
  - A/B variation comparison view
  - Edit-in-place for each variation
  - "Select & Schedule" button per variation

### 7.5 Visual Content Calendar Page
- [ ] 7.5.1 Calendar grid (month/week view)
- [ ] 7.5.2 Drag-and-drop posts between dates/times
- [ ] 7.5.3 A/B draft display per slot (side-by-side or toggle)
- [ ] 7.5.4 Click-to-edit post details
- [ ] 7.5.5 Status indicators: draft, scheduled, published, failed
- [ ] 7.5.6 Time zone display (Asia/Jakarta)

### 7.6 Agent Thinking Log Page
- [ ] 7.6.1 Real-time log viewer (WebSocket connection)
- [ ] 7.6.2 Filter by step type (research, strategy, generation, publishing)
- [ ] 7.6.3 Filter by status (info, success, warning, error)
- [ ] 7.6.4 Auto-scroll toggle
- [ ] 7.6.5 Timestamp display with timezone

### 7.7 Settings Page
- [ ] 7.7.1 AI Configuration section (edit provider, model, key)
- [ ] 7.7.2 Distribution section (edit Repliz config)
- [ ] 7.7.3 Notification section (Telegram/Discord webhook URLs)
- [ ] 7.7.4 Language & Localization section
- [ ] 7.7.5 Style Profile section (view/edit analyzed style)
- [ ] 7.7.6 Template Export button (downloads .md file)
- [ ] 7.7.7 Scheduler config (posting days, preferred hours, weekend toggle)

### 7.8 Trends Page
- [ ] 7.8.1 Trend list with filters (source, direction)
- [ ] 7.8.2 Trend detail view (research summary, related keywords)
- [ ] 7.8.3 "Use as Topic" button → navigates to content creation
- [ ] 7.8.4 Manual refresh button

### 7.9 Drafts & History Pages
- [ ] 7.9.1 Draft list with filters (source, archived, topic)
- [ ] 7.9.2 Draft detail view with edit capability
- [ ] 7.9.3 History: published posts list with metrics
- [ ] 7.9.4 Export drafts as CSV/JSON

---

## Phase 8: Data Schema Alignment

### 8.1 Config Store
- [ ] 8.1.1 Verify `Setting` model stores: API keys (encrypted), language preferences, Instruction Vault markdown
- [ ] 8.1.2 Add encryption for sensitive fields (API keys, webhook URLs)
- [ ] 8.1.3 Add `notification_webhooks` JSON field

### 8.2 Content Store
- [ ] 8.2.1 Verify `Post` model has all PRD fields:
  - `id`, `topic` (via niche relation), `hook_type`, `framework`, `content_body`, `style_id`, `status`, `scheduled_at`, `repliz_id`
- [ ] 8.2.2 Add `hook_type` field to `Post` model (currently missing)
- [ ] 8.2.3 Add `framework` field to `Post` model (currently missing)
- [ ] 8.2.4 Add `scheduled_at` field to `Post` model (currently missing)
- [ ] 8.2.5 Add `style_id` field to `Post` model (references style profile)

### 8.3 Reference Store
- [ ] 8.3.1 Create `StyleReference` model for storing "Style Reference" texts
- [ ] 8.3.2 Fields: `id`, `user_id`, `reference_text`, `analyzed_profile` (JSON), `created_at`
- [ ] 8.3.3 Create API endpoints for CRUD operations

---

## Phase 9: Testing & Quality Assurance

### 9.1 Backend Testing
- [ ] 9.1.1 Set up pytest configuration
- [ ] 9.1.2 Write unit tests for `CopywriterAgent`
- [ ] 9.1.3 Write unit tests for `TrendHunter`
- [ ] 9.1.4 Write unit tests for `AIClient`
- [ ] 9.1.5 Write unit tests for `SchedulerService`
- [ ] 9.1.6 Write integration tests for all API endpoints
- [ ] 9.1.7 Write tests for SQLite database operations

### 9.2 Frontend Testing
- [ ] 9.2.1 Set up Vitest/Jest configuration
- [ ] 9.2.2 Write component tests for Setup Wizard
- [ ] 9.2.3 Write component tests for Content Calendar
- [ ] 9.2.4 Write E2E tests for full workflow (Setup → Generate → Schedule → Publish)

### 9.3 Deployment Testing
- [ ] 9.3.1 Test `install.sh` on clean Ubuntu VPS
- [ ] 9.3.2 Verify deployment completes in < 180 seconds (PRD metric)
- [ ] 9.3.3 Verify port 8080 accessibility
- [ ] 9.3.4 Verify Docker container health checks

---

## Phase 10: Documentation & Polish

### 10.1 Documentation
- [ ] 10.1.1 Update `README.md` with new architecture
- [ ] 10.1.2 Create `docs/SETUP.md` — detailed setup guide
- [ ] 10.1.3 Create `docs/API.md` — API reference
- [ ] 10.1.4 Create `docs/DEPLOYMENT.md` — VPS deployment guide

### 10.2 Success Metrics Verification
- [ ] 10.2.1 Measure deployment time (< 180 seconds)
- [ ] 10.2.2 Measure AI output quality (< 5% manual correction)
- [ ] 10.2.3 Verify consistent posting frequency without manual input

---

## Dependency Graph

```
Phase 1 (Foundation)
  └── Phase 2 (AI Layer)
        └── Phase 3 (Content Identity)
              └── Phase 4 (Autonomous Workflow)
                    ├── Phase 5 (Monitoring)
                    └── Phase 8 (Data Schema)
                          └── Phase 7 (Frontend)
                                └── Phase 9 (Testing)
                                      └── Phase 10 (Docs)

Phase 6 (Setup Wizard Backend) — can run parallel with Phase 2-4
```

## Priority Order

1. **P0 (Critical)**: Phase 1 → Phase 8 → Phase 2 → Phase 4
2. **P1 (Important)**: Phase 3 → Phase 5 → Phase 6
3. **P2 (Frontend)**: Phase 7 (can start after P0 APIs are stable)
4. **P3 (Polish)**: Phase 9 → Phase 10

## Estimated Effort

| Phase | Effort | Notes |
|-------|--------|-------|
| Phase 1 | 1-2 days | DB migration + Docker + installer |
| Phase 2 | 2-3 days | Style mimicry + localization + research + workflow |
| Phase 3 | 1 day | Topic selector + vault + template |
| Phase 4 | 2-3 days | Full autonomous pipeline |
| Phase 5 | 1 day | Agent log + webhooks |
| Phase 6 | 0.5 day | Setup wizard endpoints |
| Phase 7 | 3-5 days | Full React/Next.js frontend |
| Phase 8 | 0.5 day | Schema alignment |
| Phase 9 | 1-2 days | Testing |
| Phase 10 | 0.5 day | Docs |
| **Total** | **~12-18 days** | Depends on team size |
