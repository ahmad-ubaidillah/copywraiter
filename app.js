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
    source_url TEXT DEFAULT '',
    context TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now'))
  );
`);

// Migrate old DB — add columns if missing
try { db.exec("ALTER TABLE trends ADD COLUMN source_url TEXT DEFAULT ''"); } catch(e) {}
try { db.exec("ALTER TABLE trends ADD COLUMN context TEXT DEFAULT ''"); } catch(e) {}
try { db.exec("CREATE UNIQUE INDEX IF NOT EXISTS idx_trends_topic ON trends(topic)"); } catch(e) {}

db.exec(`
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
    // Hapus trends lama yang bukan dari refresh ini (tapi amankan referensi draft)
    const keepTopics = results.map(t => t.topic);
    if (keepTopics.length > 0) {
      const placeholders = keepTopics.map(() => '?').join(',');
      // Hanya hapus yang tidak direferensi oleh draft
      db.prepare(`DELETE FROM trends WHERE topic NOT IN (${placeholders}) AND id NOT IN (SELECT DISTINCT topic_id FROM drafts WHERE topic_id IS NOT NULL)`).run(...keepTopics);
    }
    res.json({ status: 'ok', count: results.length, trends: results });
    // Dedup: keep only the latest entry per topic
    db.exec("DELETE FROM trends WHERE id NOT IN (SELECT MIN(id) FROM trends GROUP BY topic)");
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
  'enhypen','bts','sk8er','yoxi','donutsmp','donutsmp','born2shine','perthsanta',
  'tonton selengkapnya','baca juga','artikel terkait','selengkapnya','lihat lainnya'];

// Only keep topics that are meaningful for copywriting:
// - Minimum 5 words OR contain a verb/action word
// - Not just names/places without context
function isMeaninglessTopic(topic) {
  const words = topic.trim().split(/\s+/);
  if (words.length < 4) return true; // too short, no context
  // Check if it contains typical Indonesian verbs indicating real news
  const hasAction = /(resmi|terjadi|ungkap|bicara|ungkap|klaim|ancam|dukung|tolak|minta|beri|batal|larang|wajib|naik|turun|buka|tutup|henti|lapor|tuntut|vonis|hukum|denda|tangkap|serang|bom|tabrak|bakar|curi|rampas|gelap|selamat|tewas|tewas|korban|rugi|bantu|santuni|salur|bangun|kembang|luncur|rilis|terbit|siar|tayang|gelar|ikuti|hadir|kunjung|tinjau|sidak|razia|sita|blokir|beku|bubar|larut|demo|mogok|boikot)\b/i.test(topic);
  if (!hasAction && words.length < 6) return true; // no action verb AND too short
  return false;
}

// Trivial words that are not meaningful content
const TRIVIAL = new Set([
  'libur','pagii','pagi','siang','sore','malam','jumatan',
  'senin','selasa','rabu','kamis','sabtu','minggu',
  'januari','februari','maret','april','mei','juni','juli','agustus','september','oktober','november','desember',
  'hallo','hello','hai','hi','test','testing','coba','ah','oh','wah',
  'bismillah','alhamdulillah','subhanallah','astagfirullah',
  'kenaikan yesus kristus','natal','idul fitri','idul adha','imlek','nyepi','tahun baru',
  'beckham','canton','revan','jorji','mark lee','the economist','nobel','aston','kristiani','wakana yamazaki'
]);

function isTrivial(topic) {
  const t = topic.toLowerCase().trim();
  if (t.length < 4 && !/[A-Za-z]{3,}/.test(t)) return true;
  if (TRIVIAL.has(t) || TRIVIAL.has(t.replace(/[^a-z]/g,''))) return true;
  // Single short word without context — likely a name, not a trend
  if (!/\s/.test(t) && t.length <= 8 && !/tech|ai|pro|hub|id|news|bank|digital|indonesia/i.test(t)) return true;
  return false;
}

// Topics that are clearly not about Indonesia
const INTERNATIONAL_KEYWORDS = [
  'premier league','la liga','nba','nfl','mlb','uefa','champions league',
  'world cup','olympics','grand slam','super bowl',
  'trump','biden','putin','xi jinping','ukraine','russia','israel','palestine',
  'ollie watkins','mitch marner','tuch','chargers','raiders','titans','rams','cubs','rangers',
  'nvidia','apple','microsoft','google','meta','amazon','tsla','bitcoin','ethereum',
  'trade $','stock market','wall street','dow jones','s&p','nasdaq'
];

function scoreTopic(topic, source) {
  if (isTrivial(topic)) return 0;
  if (isMeaninglessTopic(topic)) return 0;
  // Filter international topics
  if (INTERNATIONAL_KEYWORDS.some(k => topic.toLowerCase().includes(k))) return 0;

  let score = source === 'trends24' ? 50 : 60;
  if (/\b(ai|automation|tech|digital|startup|bisnis|ekonomi|work|karir|linkedin|personal.?branding|n8n|coding|programmer|software)\b/i.test(topic)) score += 30;
  if (/tips|tutorial|cara|guide|belajar|panduan/i.test(topic)) score += 20;
  if (/sepak.?bola|liga|club|fc|vs|madrid|barcelona|juventus|premier/i.test(topic)) score -= 30;
  if (/[\u3040-\u9fff\uac00-\ud7af]/.test(topic)) score -= 40;
  if (BLACKLIST.some(b => topic.toLowerCase().includes(b))) return 0;
  return Math.max(0, Math.min(100, score));
}

function normalizeTopic(topic) {
  return topic.toLowerCase()
    .replace(/[^a-z0-9\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

async function scrapeTrends24() {
  const resp = await fetch('https://trends24.in/indonesia/', {
    headers: { 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36' }
  });
  const html = await resp.text();
  const matches = [...html.matchAll(/<a[^>]*href="[^"]*"[^>]*class=\s*"?[^"\s]*"?[^>]*>\s*([^<{][^<]{2,80}?)\s*<\/a>/g)];
  const seen = new Set();
  const topics = [];
  for (const m of matches) {
    let topic = m[1].trim().replace(/&\w+;/g, '').replace(/\s+/g, ' ').replace(/^\d+[. ]*/, '');
    if (!topic || topic.length < 3) continue;
    const key = normalizeTopic(topic);
    if (seen.has(key)) continue;
    seen.add(key);
    const score = scoreTopic(topic, 'trends24');
    if (score > 20) {
      topics.push({ topic, source: 'trends24', score,
        relevance: score > 70 ? 'high' : score > 40 ? 'medium' : 'low',
        angle: /ai|tech|digital|automation|bisnis|ekonomi/i.test(topic) ? 'thought leadership' :
               /tips|tutorial|belajar|panduan|guide/i.test(topic) ? 'tutorial' : 'general' });
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

// Location names that need context — filter out if standalone
const LOCATIONS = new Set([
  'sumatera','sumatra','jawa','kalimantan','sulawesi','papua','maluku','bali','nusa tenggara',
  'aceh','medan','padang','palembang','lampung','pekanbaru','jambi','bengkulu','tanjungpinang','pangkalpinang',
  'jakarta','bandung','semarang','surabaya','yogyakarta','solo','malang','surakarta','bekasi','tangerang','depok','bogor',
  'banjarmasin','banjarbaru','palangkaraya','pontianak','samarinda','balikpapan',
  'makassar','manado','palu','kendari','gorontalo','mamuju','ambon','ternate','soa siu','manokwari','jayapura',
  'denpasar','mataram','kupang',
  'sumatera utara','sumatera barat','sumatera selatan','riau','kepulauan riau','jambi','bengkulu','lampung','bangka belitung',
  'jawa barat','jawa tengah','jawa timur','banten',
  'kalimantan barat','kalimantan tengah','kalimantan timur','kalimantan utara','kalimantan selatan',
  'sulawesi utara','sulawesi tengah','sulawesi selatan','sulawesi barat','sulawesi tenggara','gorontalo',
  'maluku','maluku utara','papua barat','papua','papua tengah','papua pegunungan','papua selatan',
  'bali','nusa tenggara barat','nusa tenggara timur'
]);

const NEWS_SOURCES = [
  {
    url: 'https://www.kompas.com/tren',
    selector: '<h[23][^>]*class="[^"]*tren[^"]*"[^>]*>\\s*<a[^>]*href="([^"]*)"[^>]*>([^<]{15,200}?)<\\/a>\\s*<\\/h[23]>',
    name: 'kompas',
    minLen: 15,
    titleGroup: 2,
    urlGroup: 1
  },
  {
    url: 'https://www.detik.com/terpopuler',
    selector: '<article[^>]*>[\\s\\S]*?<a[^>]*href="([^"]*detik\\.com[^"]*)"[^>]*>([^<]{20,200}?)<\\/a>',
    name: 'detik',
    minLen: 20,
    titleGroup: 2,
    urlGroup: 1
  },
  {
    url: 'https://getdaytrends.com/indonesia/',
    selector: '<a class="string"[^>]*href="([^"]*)"[^>]*>([^<]+)<\\/a>',
    name: 'twitter',
    minLen: 3,
    titleGroup: 2,
    urlGroup: 1
  },
  {
    url: 'https://trends24.in/indonesia/',
    selector: '<a[^>]*href="([^"]*twitter\\.com[^"]*)"[^>]*class=\\s*"?[^"\\s]*"?[^>]*>\\s*([^<]{2,80}?)\\s*<\\/a>',
    name: 'twitter',
    minLen: 3,
    titleGroup: 2,
    urlGroup: 1
  },
  {
    url: 'https://www.liputan6.com/',
    selector: '<a[^>]*href="([^"]*liputan6\\.com/[^"]*)"[^>]*>([^<]{15,200}?)<\\/a>',
    name: 'liputan6',
    minLen: 15,
    titleGroup: 2,
    urlGroup: 1
  },
  {
    url: 'https://www.inews.id/',
    selector: '<h[^>]*>[^<]*<a[^>]*href="([^"]*)"[^>]*>([^<]{15,200}?)<\\/a>',
    name: 'inews',
    minLen: 15,
    titleGroup: 2,
    urlGroup: 1
  },
  {
    url: 'https://www.suara.com/',
    selector: '<a[^>]*href="([^"]*suara\\.com/[^"]*)"[^>]*>([^<]{15,200}?)<\\/a>',
    name: 'suara',
    minLen: 15,
    titleGroup: 2,
    urlGroup: 1
  },
  {
    url: 'https://www.merdeka.com/',
    selector: '<a[^>]*href="([^"]*merdeka\\.com/[^"]*)"[^>]*>([^<]{15,200}?)<\\/a>',
    name: 'merdeka',
    minLen: 15,
    titleGroup: 2,
    urlGroup: 1
  }
];

async function scrapeGoogleTrendsRSS() {
  try {
    const resp = await fetch('https://trends.google.com/trends/trendingsearches/daily/rss?geo=ID', {
      headers: { 'User-Agent': 'Mozilla/5.0' }
    });
    const xml = await resp.text();
    const matches = [...xml.matchAll(/<title><!\[CDATA\[([^\]]+)\]\]><\/title>/g)];
    const seen = new Set();
    const topics = [];
    for (const m of matches.slice(1)) { // skip first which is feed title
      let topic = m[1].trim();
      if (!topic || topic.length < 5) continue;
      const key = normalizeTopic(topic);
      if (seen.has(key)) continue;
      seen.add(key);
      const score = scoreTopic(topic, 'google_trends');
      if (score > 20) {
        topics.push({ topic, source: 'google_trends', score,
          relevance: score > 70 ? 'high' : score > 40 ? 'medium' : 'low',
          angle: /ai|tech|digital|automation|bisnis|ekonomi|startup/i.test(topic) ? 'thought leadership' :
                 /tips|tutorial|belajar|panduan|guide|sehat|hidup|kerja/i.test(topic) ? 'tutorial' : 'general' });
      }
    }
    return topics.slice(0, 15);
  } catch { return []; }
}

async function scrapeNewsSource(src) {
  try {
    const { url, selector, name: sourceName, minLen = 8, titleGroup = 1, urlGroup } = src;
    const resp = await fetch(url, {
      headers: { 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36' },
      signal: AbortSignal.timeout(8000)
    });
    const html = await resp.text();
    const matches = [...html.matchAll(new RegExp(selector, 'gi'))];
    const seen = new Set();
    const topics = [];
    for (const m of matches) {
      let topic = (m[titleGroup] || m[0]).trim();
      topic = topic.replace(/<[^>]+>/g, '').replace(/&\w+;/g, '').replace(/\s+/g, ' ').trim();
      if (!topic || topic.length < minLen) continue;
      const lowered = normalizeTopic(topic);
      if (LOCATIONS.has(lowered)) continue;
      // Filter out tag/collection pages from some sources
      if (sourceName === 'merdeka' && sourceUrl.includes('/tag/')) continue;
      if (sourceName === 'kompas' && (sourceUrl.includes('/tren/read/') || sourceUrl.includes('.kompas.com/read/'))) {/* OK */}
      if (sourceName === 'detik' && sourceUrl.includes('/tag/')) continue;
      const key = normalizeTopic(topic);
      if (seen.has(key)) continue;
      seen.add(key);
      const score = scoreTopic(topic, sourceName);
      if (score > 20) {
        // Extract source URL
        let sourceUrl = urlGroup && m[urlGroup] ? m[urlGroup].trim() : '';
        if (sourceUrl && !sourceUrl.startsWith('http')) {
          const base = new URL(url);
          sourceUrl = sourceUrl.startsWith('/') ? base.origin + sourceUrl : base.origin + '/' + sourceUrl;
        }
        // Generate context based on source type
        let context = '';
        if (['detik','kompas','liputan6','inews','suara','merdeka'].includes(sourceName)) {
          context = 'Sedang ramai diperbincangkan di ' + sourceName + '. ' + topic.substring(0, 80) + '...';
        } else if (sourceName === 'twitter') {
          context = 'Topik trending di Twitter Indonesia.';
        }
        topics.push({ topic, source: sourceName, score, source_url: sourceUrl, context });
      }
    }
    return topics.slice(0, 15);
  } catch { return []; }
}

async function runTrendHunter() {
  console.log('[TrendHunter] Scraping from ' + NEWS_SOURCES.length + ' sources...');
  const promises = NEWS_SOURCES.map(s => scrapeNewsSource(s));

  const results = await Promise.allSettled(promises);

  const all = [];
  for (const r of results) {
    if (r.status === 'fulfilled') all.push(...r.value);
  }

  // Dedup by normalized topic across all sources
  const seen = new Set();
  const unique = [];
  for (const t of all) {
    const key = normalizeTopic(t.topic);
    if (seen.has(key)) continue;
    seen.add(key);
    unique.push(t);
  }

  // Sort by score descending
  unique.sort((a, b) => b.score - a.score);

  // Save to DB
  const stmt = db.prepare("INSERT OR IGNORE INTO trends (topic,source,score,source_url,context) VALUES (?,?,?,?,?)");
  let saved = 0;
  for (const t of unique.slice(0, 60)) {
    try { stmt.run(t.topic, t.source, t.score, t.source_url||'', t.context||''); saved++; }
    catch(e) { /* dup */ }
  }
  console.log(`[TrendHunter] Saved ${saved} trends from ${all.length} total`);
  return unique.slice(0, 40);
}

// ── Writing Style Config ──────────────────────────────────────────
const DEFAULT_WRITING_STYLE = {
  "identity": {
    "role": "Indonesian Human Storyteller",
    "persona": "Lo adalah WARGA SIPIL yang pinter tapi udah CAPEK sama drama di TV dan sosmed. Lo nyablak, sinis, tapi logis. Lo BENCI BANGET sama orang yang HAUS PANGGUNG dan gaya bicara formal kayak asisten AI. Nada lo: capek, jujur, sarkas tapi humble."
  },
  "forbidden": [
    "bullet points, numbered lists, bold headers, garis pemisah",
    "hashtag (#) dan emoji — NOL toleransi",
    "pembukaan basi: Gue ngerti, Menarik banget, Oke jadi begini, Pertama-tama",
    "kata marketing: Jelajahi, Tingkatkan, Solusi, Inovatif, Revolusioner, Signifikan",
    "pertanyaan marketing: Apakah Anda lelah?, Pernahkah Anda...?",
    "istilah AI-ism: navigasi sistem, literasi digital, ekosistem informasi",
    "ngasih nasihat, motivasi, moral of the story, sok bijak, kalimat puitis",
    "nulis per baris kayak puisi — minimal 3-4 kalimat dalam SATU PARAGRAF",
    "bertanya balik ke pembaca",
    "bahas politik berat, SARA, atau opini medis"
  ],
  "structure": {
    "hook": "Satu kalimat tamparan realita langsung di baris pertama",
    "body": "Curhat ngelantur alami. Pake kata transisi organik: Lagian ya, Eh tapi, Ujung-ujungnya, Bener-bener dah. ANALOGI HARUS NYAMBUNG dengan skala masalah. Brand/produk boleh disebut sbg solusi kebetulan — JANGAN kayak iklan.",
    "cta": "Sindiran atau ajakan cuek: Terserahlah mau gimana, yang penting perut kenyang. Low-pressure. GAK BOLEH bertanya balik."
  },
  "language": {
    "word_replacements": "digitalisasi → urusan apa-apa pake HP | efisiensi → nggak ribet / sat-set | transparansi → kejujuran | mengalami peningkatan → naik nggak ngotak / gila harganya | berkomitmen → janji manis | literasi → pinter dikit baca berita | masyarakat → orang-orang / kita semua",
    "transition_words": "Lagian ya, Eh tapi, Ujung-ujungnya, Bener-bener dah",
    "forbidden_phrases": "Mana ribet mana mahal mana lama lagi — TAPI cuma kalo topik layanan publik/harga"
  },
  "analogy_map": "Politik/drama publik → rebutan parkir, antre sembako, gosip RT | Ekonomi/harga → gorengan, bensin, token listrik, bakso | Teknologi/gadget → HP, wifi lemot, aplikasi nggak jelas"
};

function loadWritingStyle() {
  const row = db.prepare("SELECT value FROM settings WHERE key='writing_style'").get();
  if (row) {
    try { return JSON.parse(row.value); } catch {}
  }
  return DEFAULT_WRITING_STYLE;
}

app.get('/api/writing-style', (req, res) => {
  res.json({ style: loadWritingStyle() });
});

app.put('/api/writing-style', (req, res) => {
  const style = req.body;
  if (!style || !style.identity) return res.status(400).json({ error: 'Format salah, butuh field identity' });
  db.prepare("INSERT INTO settings (key,value) VALUES ('writing_style',?) ON CONFLICT(key) DO UPDATE SET value=?")
    .run(JSON.stringify(style), JSON.stringify(style));
  res.json({ status: 'saved' });
});

app.post('/api/writing-style/reset', (req, res) => {
  db.prepare("INSERT INTO settings (key,value) VALUES ('writing_style',?) ON CONFLICT(key) DO UPDATE SET value=?")
    .run(JSON.stringify(DEFAULT_WRITING_STYLE), JSON.stringify(DEFAULT_WRITING_STYLE));
  res.json({ status: 'reset', style: DEFAULT_WRITING_STYLE });
});

// ── Copywriter ────────────────────────────────────────────────────
const OPENAI_API_KEY = process.env.OPENAI_API_KEY || process.env.SUMOPOD_API_KEY || '';
const OPENAI_BASE_URL = process.env.OPENAI_BASE_URL || 'https://ai.sumopod.com/v1';

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
    const { topic_id, topic, tone, context } = req.body;
    const { profile, voice } = loadKnowledgeBase();
    const brandVoice = voice.tone?.primary || tone || 'professional-santai';
    const displayName = profile.personal_info?.display_name || 'Personal Branding Expert';
    const headline = profile.personal_info?.headline || '';

    // Get context from trend if topic_id provided — fetch FULL article
    let trendContext = context || '';
    if (topic_id && !trendContext) {
      const trend = db.prepare("SELECT * FROM trends WHERE id=?").get(topic_id);
      if (trend) {
        trendContext = trend.context || '';
        // Fetch full article content
        if (trend.source_url) {
          try {
            const articleResp = await fetch(trend.source_url, {
              headers: { 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36' },
              signal: AbortSignal.timeout(10000)
            });
            if (articleResp.ok) {
              const html = await articleResp.text();
              // Extract article text: strip HTML tags, get meaningful content
              const text = html
                .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '')
                .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '')
                .replace(/<[^>]+>/g, ' ')
                .replace(/&[^;]+;/g, ' ')
                .replace(/\s+/g, ' ')
                .trim();
              // Take first 2000 chars of meaningful content
              const articleBody = text.substring(0, 2000).trim();
              if (articleBody.length > 100) {
                trendContext = 'ARTIKEL LENGKAP:\n' + articleBody + '\n\n(Diambil dari ' + trend.source_url + ')';
              }
            }
          } catch (e) {
            trendContext = trend.context || 'Sumber: ' + trend.source_url;
          }
        }
      }
    }

    // Build prompt from writing style config
    const style = loadWritingStyle();
    const forbid = style.forbidden || [];
    const struct = style.structure || {};
    const lang = style.language || {};
    const analogies = style.analogy_map || '';

    let prompt = `IDENTITAS:\n${style.identity?.persona || style.identity?.role || 'Indonesian Human Storyteller'}\n\n--- LARANGAN MUTLAK ---\n${forbid.map(f => '❌ ' + f).join('\n')}\n\n--- STRUKTUR WAJIB ---\n[HOOK] → ${struct.hook || 'Tamparan realita'}\n[BODY] → ${struct.body || 'Curhat ngelantur'}\n         ${analogies}\n[CTA]  → ${struct.cta || 'Sindiran atau ajakan cuek'}\n\n--- GAYA BAHASA ---\n- SATU PARAGRAF UTUH mengalir (min 3-4 kalimat per paragraf).\n- Ganti kata WAJIB:\n  ${(lang.word_replacements || '').split('|').join('\n  ')}\n- Kata transisi: ${lang.transition_words || ''}\n- ${lang.forbidden_phrases || ''}\n- Kalo hasilnya kerasa kayak bot, tulis ulang dengan nada lebih SINIS DAN BERANTAKAN.\n\nTopik: ${topic || 'personal branding'}\n`;

    if (trendContext) {
      prompt += `ARTIKEL UTUH:\n${trendContext}\n\n`;
    }

    prompt += `TULIS SEKARANG (SATU PARAGRAF UTUH, NO HASHTAG, NO EMOJI, NO BULLET, NO PEMBUKAAN BASI, NO BERTANYA BALIK):`;

    let draftBody = '';
    let hashtags = '';

    if (OPENAI_API_KEY) {
      const resp = await fetch(OPENAI_BASE_URL + '/chat/completions', {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer ' + OPENAI_API_KEY,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          model: process.env.OPENAI_MODEL || 'qwen/qwen3-30b-a3b-instruct-2507',
          messages: [
            { role: 'system', content: 'Kamu adalah penulis yang natural, kayak orang biasa ngomong. Gak usah pake markdown, bullet points, hashtag, atau format apapun. Tulis langsung aja.' },
            { role: 'user', content: prompt }
          ],
          max_tokens: 800,
          temperature: 0.9
        })
      });
      const data = await resp.json();
      const raw = data.choices?.[0]?.message?.content || '';
      draftBody = raw.trim();
    } else {
      draftBody = `[AI Copywriter: set OPENAI_API_KEY di .env untuk generate otomatis]\n\nTopik: ${topic || 'personal branding'}`;
    }

    // Humanize + enforce strict rules
    const humanized = humanize(draftBody)
      .replace(/#\w+/g, '')           // strip hashtags
      .replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F1E0}-\u{1F1FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, '') // strip emoji
      .replace(/^[-*+]\s+/gm, '')     // strip bullet points
      .replace(/^\d+[.)]\s+/gm, '')   // strip numbered lists
      .replace(/\n{3,}/g, '\n\n')     // collapse excessive newlines
      .trim();

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
// ── LinkedIn Integration ──────────────────────────────────────────
const LINKEDIN_CLIENT_ID = process.env.LINKEDIN_CLIENT_ID || '';
const LINKEDIN_CLIENT_SECRET = process.env.LINKEDIN_CLIENT_SECRET || '';
const LINKEDIN_REDIRECT_URI = process.env.LINKEDIN_REDIRECT_URI || 'http://localhost:5000/api/linkedin/callback';

// Ensure tokens table
db.exec(`CREATE TABLE IF NOT EXISTS linkedin_tokens (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  access_token TEXT NOT NULL,
  refresh_token TEXT,
  expires_at INTEGER,
  profile_urn TEXT,
  created_at TEXT DEFAULT (datetime('now'))
)`);

app.get('/api/linkedin/login', (req, res) => {
  if (!LINKEDIN_CLIENT_ID) {
    return res.json({ error: 'LINKEDIN_CLIENT_ID not configured. Set it in .env', setup_url: 'https://www.linkedin.com/developers/' });
  }
  const state = Math.random().toString(36).substring(2);
  const url = `https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=${LINKEDIN_CLIENT_ID}&redirect_uri=${encodeURIComponent(LINKEDIN_REDIRECT_URI)}&state=${state}&scope=openid%20profile%20email%20w_member_social`;
  res.redirect(url);
});

app.get('/api/linkedin/callback', async (req, res) => {
  const { code, error } = req.query;
  if (error) return res.status(400).json({ error: 'LinkedIn OAuth error: ' + error });
  if (!code) return res.status(400).json({ error: 'No authorization code' });

  try {
    // Exchange code for token
    const tokenResp = await fetch('https://www.linkedin.com/oauth/v2/accessToken', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        grant_type: 'authorization_code',
        code,
        redirect_uri: LINKEDIN_REDIRECT_URI,
        client_id: LINKEDIN_CLIENT_ID,
        client_secret: LINKEDIN_CLIENT_SECRET
      })
    });
    const tokenData = await tokenResp.json();
    if (!tokenData.access_token) return res.status(400).json({ error: 'Failed to get token', details: tokenData });

    // Get profile info
    const profileResp = await fetch('https://api.linkedin.com/v2/userinfo', {
      headers: { 'Authorization': 'Bearer ' + tokenData.access_token }
    });
    const profile = await profileResp.json();

    // Store token
    const expiresAt = tokenData.expires_in ? Date.now() + tokenData.expires_in * 1000 : 0;
    db.prepare("DELETE FROM linkedin_tokens").run(); // only one account
    db.prepare("INSERT INTO linkedin_tokens (access_token, refresh_token, expires_at, profile_urn) VALUES (?,?,?,?)")
      .run(tokenData.access_token, tokenData.refresh_token || '', expiresAt, profile.sub || '');

    res.json({ status: 'linked', profile: { name: profile.name, email: profile.email, sub: profile.sub } });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.get('/api/linkedin/status', (req, res) => {
  const token = db.prepare("SELECT * FROM linkedin_tokens ORDER BY id DESC LIMIT 1").get();
  if (!token) return res.json({ linked: false });
  const expired = token.expires_at ? Date.now() > token.expires_at : false;
  res.json({ linked: true, expired, profile_urn: token.profile_urn, created_at: token.created_at });
});

app.post('/api/linkedin/post', async (req, res) => {
  const { draft_id } = req.body;
  const token = db.prepare("SELECT * FROM linkedin_tokens ORDER BY id DESC LIMIT 1").get();
  if (!token) return res.status(400).json({ error: 'LinkedIn not connected. Go to Settings > Connect LinkedIn first.' });

  const draft = db.prepare("SELECT * FROM drafts WHERE id=?").get(draft_id);
  if (!draft) return res.status(404).json({ error: 'Draft not found' });

  try {
    const body = draft.body + '\n\n' + draft.hashtags;
    const resp = await fetch('https://api.linkedin.com/rest/posts', {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + token.access_token,
        'Content-Type': 'application/json',
        'LinkedIn-Version': '202501',
        'X-Restli-Protocol-Version': '2.0.0'
      },
      body: JSON.stringify({
        author: 'urn:li:person:' + token.profile_urn,
        lifecycleState: 'PUBLISHED',
        visibility: 'PUBLIC',
        commentary: body
      })
    });

    if (!resp.ok) {
      const err = await resp.text();
      return res.status(400).json({ error: 'LinkedIn API error', details: err });
    }

    const postUrl = resp.headers.get('location') || '';
    db.prepare("INSERT INTO posts (draft_id, platform, post_url) VALUES (?,?,?)").run(draft_id, 'linkedin', postUrl);
    db.prepare("UPDATE drafts SET status='posted', posted_at=datetime('now') WHERE id=?").run(draft_id);

    res.json({ status: 'posted', url: postUrl });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.get('/api/linkedin/profile', async (req, res) => {
  const token = db.prepare("SELECT * FROM linkedin_tokens ORDER BY id DESC LIMIT 1").get();
  if (!token) return res.json({ linked: false });

  try {
    const resp = await fetch('https://api.linkedin.com/v2/userinfo', {
      headers: { 'Authorization': 'Bearer ' + token.access_token }
    });
    const data = await resp.json();
    res.json({ linked: true, profile: data });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

function scheduledPost() {
  console.log('[scheduler] Checking for drafts to post...');
  const now = new Date().toISOString().substring(0, 16);
  const rows = db.prepare("SELECT * FROM drafts WHERE status='scheduled' AND scheduled_at <= ?").all(now);
  const token = db.prepare("SELECT * FROM linkedin_tokens ORDER BY id DESC LIMIT 1").get();
  for (const r of rows) {
    console.log('[scheduler] Auto-posting draft #' + r.id);
    if (token && token.access_token) {
      // Post via LinkedIn API
      postToLinkedIn(token, r);
    } else {
      // Fallback: mark as posted locally
      db.prepare("INSERT INTO posts (draft_id, platform, post_url) VALUES (?,?,?)").run(r.id, 'linkedin', '');
      db.prepare("UPDATE drafts SET status='posted', posted_at=datetime('now') WHERE id=?").run(r.id);
    }
  }
}

async function postToLinkedIn(token, draft) {
  try {
    const body = draft.body + '\n\n' + draft.hashtags;
    const resp = await fetch('https://api.linkedin.com/rest/posts', {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + token.access_token,
        'Content-Type': 'application/json',
        'LinkedIn-Version': '202501',
        'X-Restli-Protocol-Version': '2.0.0'
      },
      body: JSON.stringify({
        author: 'urn:li:person:' + token.profile_urn,
        lifecycleState: 'PUBLISHED',
        visibility: 'PUBLIC',
        commentary: body
      })
    });
    const postUrl = resp.ok ? (resp.headers.get('location') || '') : '';
    db.prepare("INSERT INTO posts (draft_id, platform, post_url) VALUES (?,?,?)").run(draft.id, 'linkedin', postUrl);
    db.prepare("UPDATE drafts SET status='posted', posted_at=datetime('now') WHERE id=?").run(draft.id);
    console.log('[scheduler] Posted draft #' + draft.id + ' url=' + postUrl);
  } catch (e) {
    console.error('[scheduler] Failed to post #' + draft.id + ': ' + e.message);
    // Still mark as posted so we don't retry forever
    db.prepare("INSERT INTO posts (draft_id, platform, post_url) VALUES (?,?,?)").run(draft.id, 'linkedin', '');
    db.prepare("UPDATE drafts SET status='posted', posted_at=datetime('now') WHERE id=?").run(draft.id);
  }
}
setInterval(scheduledPost, 15 * 60 * 1000);

app.listen(PORT, () => {
  console.log('copywrAIter running on http://localhost:' + PORT);
});
