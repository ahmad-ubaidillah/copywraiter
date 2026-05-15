# Tasks — copywrAIter

## T1: Setup Project Structure
- [ ] Buat folder structure (web/, agents/, data/, scripts/, logs/)
- [ ] Buat requirements.txt
- [ ] Buat .env template
- [ ] Buat .gitignore
- [ ] Init git
- **Agent:** PM
- **Dependency:** None

## T2: Build Backend API Foundation
- [ ] Buat app.py (Flask entry point)
- [ ] Buat models.py (SQLite schema: trends, drafts, posts, settings)
- [ ] Buat routes: /api/status, /api/trends, /api/drafts, /api/history, /api/settings
- [ ] Buat db.py (init database helper)
- [ ] Buat scheduler.py (APScheduler untuk jadwal posting)
- **Agent:** BE
- **Dependency:** T1

## T3: Build Web GUI (Frontend)
- [ ] Buat index.html — layout: sidebar + content area
- [ ] Buat style.css — hitam-putih, responsive
- [ ] Buat app.js — routing SPA sederhana
- [ ] Halaman Dashboard — stats, next post, recent trends
- [ ] Halaman Trends — trending list + filter + action
- [ ] Halaman Drafts — list draft + approve/reject/schedule
- [ ] Halaman History — posted + engagement
- [ ] Halaman Settings — brand voice, schedule, API keys
- [ ] Integrasi semua API endpoint
- **Agent:** FE + UI/UX
- **Dependency:** T2

## T4: Trend Hunter Agent
- [ ] Buat agents/trend_hunter.py
- [ ] Scrape Trends24 Indonesia (requests + BS4)
- [ ] Scrape Google Trends Indonesia
- [ ] Filter: relevansi, skor, keamanan
- [ ] Simpan ke tabel trends
- [ ] API endpoint /api/trends
- **Agent:** BE
- **Dependency:** T2

## T5: Copywriter + Humanizer Agent
- [ ] Buat agents/copywriter.py
- [ ] Baca knowledge base (profile, brand_voice, samples)
- [ ] Generate draft via OpenAI API
- [ ] Humanizer refine
- [ ] Scoring oleh Brand Coach logic
- [ ] Simpan ke tabel drafts
- [ ] API endpoint POST /api/draft/generate
- **Agent:** BE
- **Dependency:** T2

## T6: LinkedIn Integration
- [ ] Setup LinkedIn OAuth 2.0 (client ID, secret, redirect)
- [ ] Buat agents/linkedin_client.py
- [ ] API: post ke LinkedIn
- [ ] API: get profile data
- [ ] API: get engagement stats
- [ ] Simpan token ke database (encrypted)
- **Agent:** BE + Cybersecurity
- **Dependency:** T2

## T7: Auto-Post Scheduler
- [ ] Integrasi scheduler dengan draft queue
- [ ] Post otomatis 2x/hari (jam 07:00, 19:00 WIB)
- [ ] Log hasil posting (sukses/gagal + engagement)
- [ ] Retry logic kalau gagal
- **Agent:** DevOps + BE
- **Dependency:** T5, T6

## T8: Profile Optimizer
- [ ] Buat agents/profile_optimizer.py
- [ ] Read profile via LinkedIn API
- [ ] AI analyze + suggest improvements
- [ ] Simpan suggestion ke tabel
- [ ] User approval via GUI
- [ ] Apply via browser automation (Playwright)
- **Agent:** BE + Cybersecurity
- **Dependency:** T6

## T9: Testing & QA
- [ ] Test semua API endpoint
- [ ] Test frontend rendering
- [ ] Test flow: trend → draft → approve → post
- [ ] Test error states
- [ ] Test security (input validation, XSS, SQLi)
- **Agent:** QA
- **Dependency:** T3, T4, T5, T7

## T10: Deployment
- [ ] Setup systemd service
- [ ] Setup cron scheduler
- [ ] Setup log rotation
- [ ] Production checklist (CORS, rate limit, env vars)
- [ ] Health check monitoring
- **Agent:** DevOps + Cybersecurity
- **Dependency:** T9