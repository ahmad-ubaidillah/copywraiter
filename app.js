const express = require('express');
const path = require('path');
const fs = require('fs');
const sqlite3 = require('better-sqlite3');

const BASE = __dirname;
const DB_PATH = path.join(BASE, 'data', 'app.db');
const PORT = 5000;

// Ensure dirs
fs.mkdirSync(path.join(BASE, 'data'), { recursive: true });
fs.mkdirSync(path.join(BASE, 'logs'), { recursive: true });

// DB
const db = new sqlite3(DB_PATH);
db.pragma('journal_mode = WAL');

db.exec(`
  CREATE TABLE IF NOT EXISTS trends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'manual',
    score INTEGER DEFAULT 0,
    relevance TEXT DEFAULT '',
    angle TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now'))
  );
  CREATE TABLE IF NOT EXISTS drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id INTEGER REFERENCES trends(id),
    platform TEXT DEFAULT 'linkedin',
    body TEXT NOT NULL,
    hashtags TEXT DEFAULT '',
    status TEXT DEFAULT 'draft',
    score INTEGER DEFAULT 0,
    scheduled_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    posted_at TEXT
  );
  CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    draft_id INTEGER REFERENCES drafts(id),
    platform TEXT DEFAULT 'linkedin',
    post_url TEXT,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    views INTEGER DEFAULT 0,
    posted_at TEXT DEFAULT (datetime('now'))
  );
  CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
  );
  CREATE TABLE IF NOT EXISTS profile_suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    field TEXT NOT NULL,
    old_text TEXT,
    new_text TEXT NOT NULL,
    reason TEXT,
    status TEXT DEFAULT 'pending',
    created_at TEXT DEFAULT (datetime('now'))
  );
`);

const app = express();
app.use(express.json());
app.use(express.static(path.join(BASE, 'web', 'public')));

// API Routes
app.get('/api/status', (req, res) => {
  const s = db.prepare("SELECT COUNT(*) as c FROM drafts").get();
  const p = db.prepare("SELECT COUNT(*) as c FROM posts").get();
  const t = db.prepare("SELECT COUNT(*) as c FROM trends").get();
  res.json({ status: 'ok', version: '1.0.0', stats: { drafts: s.c, posts: p.c, trends: t.c } });
});

app.post('/api/trends/refresh', async (req, res) => {
  try {
    const results = await runTrendHunter();
    res.json({ status: 'ok', count: results.length, trends: results });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.get('/api/trends', (req, res) => {
  const rows = db.prepare("SELECT * FROM trends ORDER BY score DESC, created_at DESC LIMIT 50").all();
  res.json({ trends: rows });
});

app.post('/api/trends', (req, res) => {
  const { topic, source, score, relevance, angle } = req.body;
  const r = db.prepare("INSERT INTO trends (topic,source,score,relevance,angle) VALUES (?,?,?,?,?)")
    .run(topic, source||'manual', score||0, relevance||'', angle||'');
  res.status(201).json({ id: r.lastInsertRowid });
});

app.get('/api/drafts', (req, res) => {
  const status = req.query.status || '';
  let rows;
  if (status) {
    rows = db.prepare("SELECT d.*, t.topic FROM drafts d LEFT JOIN trends t ON d.topic_id=t.id WHERE d.status=? ORDER BY d.created_at DESC").all(status);
  } else {
    rows = db.prepare("SELECT d.*, t.topic FROM drafts d LEFT JOIN trends t ON d.topic_id=t.id ORDER BY d.created_at DESC").all();
  }
  res.json({ drafts: rows });
});

app.post('/api/draft/generate', (req, res) => {
  const { body, hashtags, topic_id } = req.body;
  const r = db.prepare("INSERT INTO drafts (topic_id, body, hashtags, status) VALUES (?,?,?,?)")
    .run(topic_id||null, body, hashtags||'', 'draft');
  res.status(201).json({ id: r.lastInsertRowid, status: 'draft' });
});

app.post('/api/draft/:id/approve', (req, res) => {
  db.prepare("UPDATE drafts SET status='approved' WHERE id=?").run(req.params.id);
  res.json({ status: 'approved' });
});

app.post('/api/draft/:id/reject', (req, res) => {
  db.prepare("UPDATE drafts SET status='rejected' WHERE id=?").run(req.params.id);
  res.json({ status: 'rejected' });
});

app.post('/api/draft/:id/schedule', (req, res) => {
  db.prepare("UPDATE drafts SET status='scheduled', scheduled_at=? WHERE id=?")
    .run(req.body.scheduled_at, req.params.id);
  res.json({ status: 'scheduled' });
});

app.get('/api/history', (req, res) => {
  const rows = db.prepare("SELECT p.*, d.body as draft_body, d.hashtags FROM posts p JOIN drafts d ON p.draft_id=d.id ORDER BY p.posted_at DESC LIMIT 50").all();
  res.json({ posts: rows });
});

app.post('/api/post/now', (req, res) => {
  const { draft_id } = req.body;
  const draft = db.prepare("SELECT * FROM drafts WHERE id=?").get(draft_id);
  if (!draft) return res.status(404).json({ error: 'Not found' });
  db.prepare("INSERT INTO posts (draft_id, platform) VALUES (?,?)").run(draft_id, 'linkedin');
  db.prepare("UPDATE drafts SET status='posted', posted_at=datetime('now') WHERE id=?").run(draft_id);
  res.json({ status: 'posted' });
});

app.get('/api/settings', (req, res) => {
  const rows = db.prepare("SELECT key, value FROM settings").all();
  const obj = {};
  rows.forEach(r => obj[r.key] = r.value);
  res.json(obj);
});

app.put('/api/settings', (req, res) => {
  const stmt = db.prepare("INSERT INTO settings (key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=?");
  for (const [k, v] of Object.entries(req.body)) {
    stmt.run(k, v, v);
  }
  res.json({ status: 'saved' });
});

app.get('/api/profile', (req, res) => {
  const profilePath = path.join(BASE, 'knowledge_base', 'profile.json');
  if (!fs.existsSync(profilePath)) return res.json({ profile: {} });
  res.json({ profile: JSON.parse(fs.readFileSync(profilePath, 'utf8')) });
});

app.get('/api/profile/suggestions', (req, res) => {
  const rows = db.prepare("SELECT * FROM profile_suggestions ORDER BY created_at DESC").all();
  res.json({ suggestions: rows });
});

app.post('/api/profile/suggestion/:id/approve', (req, res) => {
  db.prepare("UPDATE profile_suggestions SET status='approved' WHERE id=?").run(req.params.id);
  res.json({ status: 'approved' });
});

// SPA fallback — catch-all for non-API, non-static routes
app.use((req, res, next) => {
  if (req.method === 'GET' && !req.path.startsWith('/api')) {
    return res.sendFile(path.join(BASE, 'web', 'public', 'index.html'));
  }
  next();
});

// ── Trend Hunter ──────────────────────────────────────────────────
const BLACKLIST = ['k-pop','fanwar','fanbase','kazz','yoshi','dunk','joong',
  'enhypen','bts','sk8er','yoxi','donutsmp'];

function scoreTopic(topic, source) {
  let score = source === 'trends24' ? 50 : 60;
  // Boost for tech/business topics
  if (/\b(ai|automation|tech|digital|startup|bisnis|ekonomi|work|karir|linkedin|personal.?branding|n8n|coding|programmer|software)\b/i.test(topic)) score += 30;
  if (/tips|tutorial|cara|guide|belajar|panduan/i.test(topic)) score += 20;
  if (/politik|presiden|menteri|pemerintah|parpol|nadiem|gibran|prabowo|menteri|kpk|korupsi/i.test(topic)) score -= 50;
  if (/sepak.?bola|liga|club|fc|vs|madrid|barcelona|juventus|premier/i.test(topic)) score -= 30;
  if (/kenaikan.*kristus|natal|idul.?fitri|imlek|nyepi/i.test(topic)) score -= 30;
  if (/[\u3040-\u9fff\uac00-\ud7af]/.test(topic)) score -= 40; // CJK/Korean chars
  if (BLACKLIST.some(b => topic.toLowerCase().includes(b))) score = 0;
  return Math.max(0, Math.min(100, score));
}

async function scrapeTrends24() {
  const resp = await fetch('https://trends24.in/indonesia/', {
    headers: { 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36' }
  });
  const html = await resp.text();
  // Extract trending topics from trends24 timeline
  const matches = [...html.matchAll(/<a[^>]*href="[^"]*"[^>]*class=\s*"?[^"\s]*"?[^>]*>\s*([^<{][^<]{2,80}?)\s*<\/a>/g)];
  const seen = new Set();
  const topics = [];
  for (const m of matches) {
    const topic = m[1].trim().replace(/&\w+;/g, '').replace(/\s+/g, ' ').replace(/^\d+[. ]*/, '');
    if (!topic || topic.length < 4 || seen.has(topic)) continue;
    seen.add(topic);
    const score = scoreTopic(topic, 'trends24');
    if (score > 20) {
      topics.push({ topic, source: 'trends24', score,
        relevance: score > 70 ? 'high' : score > 40 ? 'medium' : 'low',
        angle: /ai|tech|digital|automation/i.test(topic) ? 'thought leadership' :
               /tips|tutorial|belajar/i.test(topic) ? 'tutorial' : 'general' });
    }
  }
  return topics.slice(0, 25);
}

async function scrapeGoogleTrends() {
  try {
    const resp = await fetch('https://trends.google.com/trending?geo=ID&sort=trending', {
      headers: { 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36' }
    });
    const html = await resp.text();
    const matches = [...html.matchAll(/"title":\{"query":"([^"]+)"/g)];
    const topics = [];
    const seen = new Set();
    for (const m of matches) {
      const topic = m[1].trim();
      if (!topic || seen.has(topic)) continue;
      seen.add(topic);
      const score = scoreTopic(topic, 'google_trends');
      if (score > 20) {
        topics.push({ topic, source: 'google_trends', score,
          relevance: score > 70 ? 'high' : score > 40 ? 'medium' : 'low',
          angle: 'general' });
      }
    }
    return topics.slice(0, 15);
  } catch { return []; }
}

async function runTrendHunter() {
  console.log('[TrendHunter] Scraping trends...');
  const [t24, gt] = await Promise.allSettled([scrapeTrends24(), scrapeGoogleTrends()]);
  const all = [];
  if (t24.status === 'fulfilled') all.push(...t24.value);
  if (gt.status === 'fulfilled') all.push(...gt.value);

  // Dedup by normalized topic
  const seen = new Set();
  const unique = [];
  for (const t of all) {
    const key = t.topic.toLowerCase().replace(/[^a-z0-9]/g, '');
    if (seen.has(key)) continue;
    seen.add(key);
    unique.push(t);
  }

  // Sort by score descending
  unique.sort((a, b) => b.score - a.score);

  // Save top 30 to DB
  const stmt = db.prepare("INSERT OR IGNORE INTO trends (topic,source,score,relevance,angle) VALUES (?,?,?,?,?)");
  let saved = 0;
  for (const t of unique.slice(0, 30)) {
    try {
      stmt.run(t.topic, t.source, t.score, t.relevance, t.angle);
      saved++;
    } catch(e) { /* dup */ }
  }
  console.log(`[TrendHunter] Saved ${saved} trends`);
  return unique.slice(0, 10);
}

// ── Copywriter ────────────────────────────────────────────────────
const OPENAI_API_KEY = process.env.OPENAI_API_KEY || '';

function loadKnowledgeBase() {
  const profilePath = path.join(BASE, 'knowledge_base', 'profile.json');
  const voicePath = path.join(BASE, 'knowledge_base', 'brand_voice.json');
  const profile = fs.existsSync(profilePath) ? JSON.parse(fs.readFileSync(profilePath, 'utf8')) : {};
  const voice = fs.existsSync(voicePath) ? JSON.parse(fs.readFileSync(voicePath, 'utf8')) : {};
  return { profile, voice };
}

function humanize(text) {
  const patterns = [
    ['Dalam era digital yang semakin maju', 'Dunia digital sekarang'],
    ['Tidak dapat dipungkiri bahwa', 'Gak bisa dipungkiri'],
    ['Perlu diingat bahwa', 'Inget aja'],
    ['Sangat penting untuk', 'Penting banget buat'],
    ['Mari kita bahas lebih dalam', 'Yuk kita bedah'],
    ['Berdasarkan pengalaman saya', 'Dari pengalaman gue'],
    ['Dapat disimpulkan bahwa', 'Intinya'],
    ['Oleh karena itu', 'Makanya'],
    ['Ke depannya', 'Ke depan'],
    ['Hal ini dikarenakan', 'Soalnya'],
    ['Merupakan sebuah', 'Adalah'],
    ['Terdapat beberapa', 'Ada beberapa'],
  ];
  let result = text;
  for (const [old, neu] of patterns) {
    result = result.replace(new RegExp(old.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi'), neu);
  }
  return result;
}

function brandCoachScore(draft, profile, voice) {
  let score = 7;
  if (draft.length > 300) score += 1;
  if (draft.length > 800) score += 1;
  if (draft.includes('?') || draft.includes('kamu') || draft.includes('lo')) score += 1;
  if (/gue|saya|aku/.test(draft)) score += 1;
  if (/politik|presiden|menteri/.test(draft)) score -= 3;
  if (draft.length < 200) score -= 2;
  return Math.max(1, Math.min(10, score));
}

app.post('/api/draft/generate-ai', async (req, res) => {
  try {
    const { topic_id, topic, tone } = req.body;
    const { profile, voice } = loadKnowledgeBase();
    const brandVoice = voice.tone?.primary || tone || 'professional-santai';
    const displayName = profile.personal_info?.display_name || 'Personal Branding Expert';
    const headline = profile.personal_info?.headline || '';

    // Build prompt
    const prompt = `Kamu adalah ${displayName} (${headline}). 
Tone: ${brandVoice}, natural, storytelling.
Bahasa: Indonesia, seperti ngobrol santai tapi profesional.
Topik: ${topic || 'personal branding'}

Buat DRAFT LINKEDIN (max 1000 karakter):
- Hook baris pertama bikin penasaran
- Ada sudut pandang pribadi / pengalaman
- Kasih value atau insight
- Akhiri dengan pertanyaan diskusi
- JANGAN pake klise

Tambahkan 3-5 hashtag di baris terakhir.
Output: {"body": "...", "hashtags": "..."}`;

    let draftBody = '';
    let hashtags = '#PersonalBranding #LinkedIn';

    if (OPENAI_API_KEY) {
      const resp = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer ' + OPENAI_API_KEY,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          model: 'gpt-4o-mini',
          messages: [{ role: 'user', content: prompt }],
          max_tokens: 800,
          temperature: 0.8
        })
      });
      const data = await resp.json();
      const raw = data.choices?.[0]?.message?.content || '';
      try {
        const parsed = JSON.parse(raw);
        draftBody = parsed.body || raw;
        hashtags = parsed.hashtags || hashtags;
      } catch {
        draftBody = raw;
      }
    } else {
      // Fallback template
      draftBody = `[AI Copywriter: set OPENAI_API_KEY di .env untuk generate otomatis]\n\nTopik: ${topic || 'personal branding'}\n\n${topic ? 'Ngomong-ngomong soal ' + topic + ', gue ada beberapa pemikiran...' : 'Gue mau bagi pengalaman tentang personal branding di LinkedIn...'}\n\nYang gue pelajari: konsistensi dan autentisitas itu jauh lebih penting daripada posting setiap hari. Lebih baik 2 post berkualitas per minggu daripada 7 post yang gak jelas.`;
    }

    // Humanize
    const humanized = humanize(draftBody);

    // Brand Coach scoring
    const score = brandCoachScore(humanized, profile, voice);

    // Save to drafts
    const r = db.prepare("INSERT INTO drafts (topic_id, body, hashtags, status, score) VALUES (?,?,?,?,?)")
      .run(topic_id || null, humanized, hashtags, score >= 6 ? 'draft' : 'draft', score);

    res.status(201).json({
      id: r.lastInsertRowid,
      body: humanized,
      hashtags,
      score,
      status: score >= 6 ? 'draft' : 'needs_review',
      humanized_from: OPENAI_API_KEY ? 'openai' : 'template'
    });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});
function scheduledPost() {
  console.log('[scheduler] Checking for drafts to post...');
  const now = new Date().toISOString().substring(0, 16);
  const rows = db.prepare("SELECT * FROM drafts WHERE status='scheduled' AND scheduled_at <= ?").all(now);
  for (const r of rows) {
    console.log('[scheduler] Auto-posting draft #' + r.id);
    db.prepare("INSERT INTO posts (draft_id, platform) VALUES (?,?)").run(r.id, 'linkedin');
    db.prepare("UPDATE drafts SET status='posted', posted_at=datetime('now') WHERE id=?").run(r.id);
  }
}
setInterval(scheduledPost, 15 * 60 * 1000);

app.listen(PORT, () => {
  console.log('copywrAIter running on http://localhost:' + PORT);
});
