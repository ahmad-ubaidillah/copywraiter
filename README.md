# copywrAIter — Autonomous Research & Copywriting Agent v1.5

AI-powered content lifecycle automation: research → strategy → generate → schedule → publish.

## Quick Start

### Docker (Recommended)
```bash
curl -sSL https://copywriter.ai/install.sh | bash
# or locally:
docker compose up -d --build
```

### Local Development
```bash
# Install UV (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Backend
cd backend
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
cp .env.example .env
uv run uvicorn main:app --reload --port 8080

# Frontend
cd frontend
npm install
npm run dev
```

Access:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8080
- Setup Wizard: http://localhost:3000/setup
- API Docs: http://localhost:8080/docs

## Architecture

```
├── backend/                  # Python FastAPI
│   ├── main.py               # App entry point (18 routers)
│   ├── config.py             # Pydantic settings
│   ├── requirements.txt      # Python dependencies
│   ├── Dockerfile            # Backend container
│   ├── app/
│   │   ├── database.py       # SQLite engine + session
│   │   ├── models.py         # SQLAlchemy models (12 tables)
│   │   ├── schemas.py        # Pydantic schemas
│   │   ├── scheduler.py      # APScheduler automation
│   │   ├── agents/
│   │   │   ├── copywriter.py     # AI copy generation
│   │   │   ├── strategist.py     # Framework/hook selection
│   │   │   ├── workflow.py       # Research→Strategy→Generate pipeline
│   │   │   └── style_analyzer.py # Style mimicry engine
│   │   ├── services/
│   │   │   ├── research_engine.py  # Tavily/Crawl4AI research
│   │   │   ├── localization.py     # Multi-language support
│   │   │   ├── repliz_client.py    # Repliz API client
│   │   │   ├── notifier.py         # Telegram/Discord webhooks
│   │   │   ├── agent_logger.py     # Agent execution log
│   │   │   └── template_exporter.py # .md template export
│   │   └── routers/            # 18 API route modules
│   ├── services/
│   │   └── trend_hunter.py     # Trend aggregation (Reddit, Google, Twitter)
│   └── tests/
│       └── test_core.py        # Unit tests (9 tests)
├── frontend/                 # Next.js 15 + Tailwind CSS v4
│   ├── app/
│   │   ├── layout.tsx            # Root layout
│   │   ├── page.tsx              # Dashboard
│   │   ├── setup/page.tsx        # Setup Wizard (5 steps)
│   │   ├── create/page.tsx       # Content creation
│   │   ├── calendar/page.tsx     # Visual calendar
│   │   ├── drafts/page.tsx       # Draft management
│   │   ├── trends/page.tsx       # Trend explorer
│   │   ├── log/page.tsx          # Agent thinking log
│   │   └── settings/page.tsx     # Settings
│   ├── components/
│   │   ├── sidebar.tsx           # Navigation sidebar
│   │   └── app-layout.tsx        # App shell
│   └── lib/api.ts            # API client
├── docker-compose.yml        # Backend + Frontend services
├── install.sh                # One-line installer
├── knowledge_base/           # Brand voice, profile, calendar
├── data/                     # SQLite database
└── logs/                     # Application logs
```

## API Endpoints

### Core CRUD
| Router | Prefix | Description |
|--------|--------|-------------|
| agents | `/agents` | AI agent management |
| drafts | `/drafts` | Draft CRUD |
| posts | `/posts` | Post CRUD |
| trends | `/trends` | Trend data |
| niches | `/niches` | Niche/topic management |
| vault | `/vault` | Instruction vault items |
| repliz | `/repliz` | Generated replies |
| linkedin | `/linkedin` | LinkedIn post tracking |
| profile | `/profile` | User profile |
| settings | `/settings` | User settings |
| style-references | `/style-references` | Style reference texts |

### PRD v1.5 Features
| Router | Prefix | Description |
|--------|--------|-------------|
| style | `/api/style` | Style mimicry (analyze, save, profile) |
| workflow | `/api/workflow` | Research→Strategy→Generate pipeline |
| research | `/api/research` | Web research (Tavily/Crawl4AI) |
| config | `/api/config` | Setup wizard endpoints |
| calendar | `/api/calendar` | Content calendar CRUD |
| publish | `/api/repliz` | Repliz publishing |
| agent-log | `/api/agent-log` | Live agent execution log |
| topics | `/api/topics` | Trending + custom topics |
| template | `/api/template` | .md template export |

## AI Intelligence

### Copywriting Frameworks
AIDA, PAS, BAB, FAB, The 4 C's

### Hook Types
Negative, Statistical, Curiosity, Authority, Question-Based

### Languages
English, Indonesian (Formal), Indonesian (Casual/Gaul), Custom

### Style Mimicry
Analyzes: sentence length, emoji density, vocabulary richness, tone markers, paragraph structure

## Deployment

### VPS (One-line)
```bash
curl -sSL https://copywriter.ai/install.sh | bash
```

### Manual Docker
```bash
docker compose up -d --build
```

### Environment Variables
See `backend/.env.example` for all configurable options.

## Testing
```bash
cd backend
python -m pytest tests/ -v
```

## License
ISC
