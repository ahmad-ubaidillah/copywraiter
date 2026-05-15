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

// Scheduler check every 15 minutes
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
