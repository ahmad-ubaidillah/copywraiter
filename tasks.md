# Tasks — copywrAIter

## T1: Setup Project Structure
- [x] Buat folder structure (web/, agents/, data/, scripts/, logs/)
- [x] Buat requirements.txt
- [x] Buat .env template
- [x] Buat .gitignore
- [x] Init git
- **Agent:** PM
- **Status:** ✅ DONE

## T2: Build Backend API Foundation
- [x] Buat app.js (Node.js + Express entry point)
- [x] Buat SQLite schema (trends, drafts, posts, settings, profile_suggestions)
- [x] Buat routes: status, trends, drafts CRUD, approve/reject/schedule, post, history, settings, profile
- [x] Buat database helper
- [x] Buat scheduler (interval check tiap 15 menit)
- **Agent:** BE
- **Status:** ✅ DONE

## T3: Build Web GUI (Frontend)
- [x] Buat index.html — layout: sidebar + content area
- [x] Buat style.css — hitam-putih, responsive
- [x] Buat app.js — routing SPA sederhana
- [x] Halaman Dashboard — stats, next post, recent trends
- [x] Halaman Trends — trending list + action
- [x] Halaman Drafts — list draft + approve/reject/schedule/post now
- [x] Halaman History — posted + engagement
- [x] Halaman Settings — brand voice, posting times
- [x] Halaman Profile — view + AI suggestions
- [x] Integrasi semua API endpoint
- **Agent:** FE + UI/UX
- **Status:** ✅ DONE

## T4: Trend Hunter Agent
- [x] Integrasi scraping Trends24 Indonesia (real HTML parse)
- [x] Scrape Google Trends Indonesia (tidak merespon karena CAPTCHA — fallback oke)
- [x] Validasi & filter: skor, blacklist, relevansi, keamanan
- [x] Endpoint POST /api/trends/refresh — trigger scrape
- [x] Scoring otomatis: tech/business boost, political/cultural penalty
- [x] Simpan ke tabel trends via API
- **Agent:** BE
- **Status:** ✅ DONE

## T5: Copywriter + Humanizer Agent
- [x] Integrasi OpenAI API untuk generate draft
- [x] Baca knowledge base (profile, brand_voice) sebagai context
- [x] Prompt engineering: personal brand voice + LinkedIn format
- [x] Humanizer refine (12 pattern replacements)
- [x] Brand Coach scoring (length, hook, tone)
- [x] Endpoint POST /api/draft/generate-ai
- [x] Frontend: ✨ Generate with AI button + tone selector
- [x] Fallback template ketika API key tidak tersedia
- **Agent:** BE
- **Status:** ✅ DONE

## T6: LinkedIn Integration
- [x] Setup LinkedIn OAuth 2.0 flow (login, callback, token storage)
- [x] Buat endpoint POST /api/linkedin/post — post draft ke LinkedIn
- [x] Buat endpoint GET /api/linkedin/profile — ambil profil LinkedIn
- [x] Buat endpoint GET /api/linkedin/status — cek koneksi
- [x] Scheduler otomatis posting via LinkedIn API jika terhubung
- [x] Frontend: status koneksi + tombol Connect di Settings
- [x] Token disimpan di database (encrypted at rest)
- **Agent:** BE + Cybersecurity
- **Status:** ✅ DONE (butuh user setup LinkedIn App)

## T7: Auto-Post Scheduler
- [x] Scheduler ambil draft scheduled + post otomatis
- [x] Post via LinkedIn API jika terhubung, fallback local jika tidak
- [x] Log hasil posting ke tabel posts
- [x] Interval check tiap 15 menit
- [ ] Jadwal spesifik 2x/hari (07:00, 19:00) — tinggal set scheduled_at di draft
- [ ] Retry logic kalau gagal (saat ini langsung mark posted)
- **Agent:** DevOps + BE
- **Status:** 🔄 PARTIAL (basic scheduler works, refinement optional)

## T8: Profile Optimizer
- [ ] Read profile via LinkedIn API
- [ ] AI analyze + suggest improvements (headline, about, experience)
- [ ] Simpan suggestion ke tabel
- [ ] User approval via GUI
- [ ] Apply via browser automation (Playwright)
- **Agent:** BE + Cybersecurity
- **Dependency:** T6
- **Status:** ⏳ PENDING

## T9: Testing & QA
- [ ] Test semua API endpoint
- [ ] Test frontend rendering
- [ ] Test flow: trend → draft → approve → post
- [ ] Test error states
- [ ] Test security (input validation, XSS)
- **Agent:** QA
- **Dependency:** T3, T4, T5, T7
- **Status:** ⏳ PENDING

## T10: Deployment
- [ ] Setup systemd service
- [ ] Setup log rotation
- [ ] Production checklist (CORS, rate limit, env vars)
- [ ] Health check monitoring
- **Agent:** DevOps + Cybersecurity
- **Dependency:** T9
- **Status:** ⏳ PENDING
