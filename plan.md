# copywrAIter — Autonomous Personal Branding Agent

## Vision
AI agent otonom yang mengelola personal branding LinkedIn secara end-to-end:
riset trending topik → generate copy → posting → optimasi profil.

## Arsitektur Agent

```
[Trend Hunter] → [Copywriter] → [Humanizer] → [Brand Coach] → [Poster]
     Agent 1        Agent 2       Agent 3        Agent 4         Agent 5
```

## Tech Stack
- **Backend:** Python Flask + SQLite
- **Frontend:** HTML/CSS/JS vanilla (hitam-putih)
- **AI:** OpenAI API (GPT-4o-mini)
- **Scheduler:** APScheduler
- **Scraping:** requests + BeautifulSoup
- **LinkedIn API:** Official REST API (OAuth 2.0)
- **Orchestrator:** Hermes Kanban

## Phase 1 — Foundation (Sekarang)
1. Setup project structure + knowledge base
2. Build backend API (Flask)
3. Build frontend GUI (hitam-putih)
4. Setup database + scheduler
5. Integrasi LinkedIn API
6. Agent 1: Trend Hunter (scrape Trends24 + Google Trends)
7. Agent 2: Copywriter (generate draft via AI)
8. Agent 3: Humanizer (refine tone)
9. Agent 4: Brand Coach (quality gate)
10. Agent 5: LinkedIn Poster (auto-post)
11. Profile Optimizer (browser automation)
12. Testing + deployment