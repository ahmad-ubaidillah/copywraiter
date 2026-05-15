# copywrAIter — Autonomous Personal Branding Agent

AI agent yang mengelola personal branding LinkedIn secara otonom:
riset trending topic → generate copy → posting → optimasi profil.

## Quick Start
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# isi .env dengan credentials
python app.py
```

## Struktur
```
├── app.py              # Flask entry point
├── web/
│   ├── server.py       # Routes & API
│   ├── models.py       # Database schema
│   ├── scheduler.py    # APScheduler
│   └── public/         # Frontend (static)
│       ├── index.html
│       ├── app.js
│       └── style.css
├── agents/
│   ├── trend_hunter.py
│   ├── copywriter.py
│   ├── humanizer.py
│   ├── brand_coach.py
│   ├── linkedin_client.py
│   └── profile_optimizer.py
├── knowledge_base/
│   ├── profile.json
│   ├── brand_voice.json
│   ├── content_calendar.json
│   └── samples/
├── data/
├── logs/
└── scripts/
```

## Agents
| Agent | Tugas |
|-------|-------|
| Trend Hunter | Scrape trending topics dari Trends24 + Google Trends |
| Copywriter | Generate draft LinkedIn copy via AI |
| Humanizer | Bikin tone lebih natural |
| Brand Coach | Quality gate, scoring, brand consistency |
| LinkedIn Poster | Post ke LinkedIn via API |
| Profile Optimizer | Saran improve profile LinkedIn |
