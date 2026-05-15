// copywrAIter — Copywriter Agent
// Generate copy dari topic, pake SumoPod AI
// Tone: warkop (capek, jujur, sarkas)
// CLI: node agents/copywriter.js "topik" [type]

const API_KEY = process.env.SUMOPOD_API_KEY || process.env.OPENAI_API_KEY || '';
const BASE_URL = process.env.OPENAI_BASE_URL || 'https://ai.sumopod.com/v1';
const MODEL = process.env.OPENAI_MODEL || 'qwen3.6-plus';
const DB_PATH = __dirname + '/../data/app.db';

const Database = require('better-sqlite3');
const fs = require('fs');

// ── Writing Style dari DB ──
function loadStyle() {
  try {
    const db = new Database(DB_PATH);
    const row = db.prepare("SELECT value FROM settings WHERE key='writing_style'").get();
    db.close();
    if (row) return JSON.parse(row.value);
  } catch(e) {}
  return null;
}

// ── Ambil konteks artikel dari DB ──
function getTrendContext(trendId) {
  const db = new Database(DB_PATH);
  const row = db.prepare("SELECT source_url, context, topic FROM trends WHERE id=?").get(trendId);
  db.close();
  return row || null;
}

// ── Generate copy ──
async function generate(topic, type = 'linkedin', trendId = null) {
  if (!API_KEY) {
    console.error('[Copywriter] SUMOPOD_API_KEY tidak diset');
    process.exit(1);
  }

  const style = loadStyle();
  let articleContext = '';

  // Fetch artikel kalo ada source_url
  if (trendId) {
    const trend = getTrendContext(trendId);
    if (trend) {
      topic = trend.topic;
      if (trend.context) {
        articleContext = trend.context;
      } else if (trend.source_url) {
        try {
          const resp = await fetch(trend.source_url, {
            headers: { 'User-Agent': 'Mozilla/5.0' },
            signal: AbortSignal.timeout(10000)
          });
          const html = await resp.text();
          articleContext = html
            .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '')
            .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '')
            .replace(/<[^>]+>/g, ' ')
            .replace(/&[^;]+;/g, ' ')
            .replace(/\s+/g, ' ').trim()
            .substring(0, 2000);
        } catch(e) {
          articleContext = '(gagal fetch artikel)';
        }
      }
    }
  }

  // Build prompt
  const prompt = `KAMU ADALAH COPYWRITER WARGA SIPIL INDONESIA.

PINTER tapi CAPEK sama drama. Nada: jujur, sarkas, humble.

JENIS: ${type}
TOPIK: ${topic}

=== LARANGAN MUTLAK ===
- SATU PARAGRAF UTUH. Bukan bullet list atau puisi per baris.
- NO hashtag (#), NO emoji
- NO bold, NO garis pemisah (---)
- NO engagement bait: "gimana menurut lo", "lo pernah ngalamin"
- NO kata marketing: Jelajahi, Tingkatkan, Solusi, Inovatif, Revolusioner
- NO AI-ism: "literasi digital", "ekosistem informasi"
- Jangan tanya balik ke pembaca

=== STRUKTUR ===
1. HOOK — tamparan realita baris pertama
2. BODY — SATU PARAGRAF ngelantur alami. Pake: "Lagian ya", "Eh tapi", "Ujung-ujungnya"
3. CTA — sindiran cuek. BUKAN pertanyaan.

=== KONTEKS ARTIKEL ===
${articleContext || '(tidak ada)'}

=== OUTPUT ===
Langsung copy siap publish. Satu paragraf utuh.`;

  try {
    const resp = await fetch(BASE_URL + '/chat/completions', {
      method: 'POST',
      headers: { 'Authorization': 'Bearer ' + API_KEY, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: MODEL,
        messages: [
          { role: 'system', content: 'Kamu copywriter Indonesia. Nada warkop, jujur, sarkas. Output langsung tanpa embel-embel.' },
          { role: 'user', content: prompt }
        ],
        temperature: 0.8,
        max_tokens: 1024
      })
    });
    const data = await resp.json();
    let copy = data.choices?.[0]?.message?.content || '';

    // Strip banned stuff
    copy = copy
      .replace(/#\w+/g, '')
      .replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F1E0}-\u{1F1FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, '')
      .replace(/^[-*+]\s+/gm, '')
      .replace(/^\d+[.)]\s+/gm, '')
      .replace(/\n{3,}/g, '\n\n')
      .trim();

    return { topic, type, body: copy, chars: copy.length };
  } catch(e) {
    throw new Error('Gagal generate: ' + e.message);
  }
}

// ── Save ke DB ──
function saveToDB(result) {
  const db = new Database(DB_PATH);
  // Cari topic_id pake LIKE (soalnya topic di DB mungkin lebih panjang)
  const trend = db.prepare("SELECT id FROM trends WHERE topic LIKE ? LIMIT 1").get('%' + result.topic.substring(0, 40) + '%');
  const topicId = trend ? trend.id : null;
  
  if (!topicId) {
    // Fallback: cari trend paling baru
    const latest = db.prepare("SELECT id FROM trends ORDER BY id DESC LIMIT 1").get();
    if (latest) topicId = latest.id;
  }
  
  const stmt = db.prepare(
    "INSERT INTO drafts (topic_id, body, status, score, created_at) VALUES (?,?,'draft',7,datetime('now'))"
  );
  const info = stmt.run(topicId || 0, result.body);
  db.close();
  console.log(`[Copywriter] Draft #${info.lastInsertRowid} tersimpan`);
  return info.lastInsertRowid;
}

// ── CLI ──
if (require.main === module) {
  const topic = process.argv[2];
  const type = process.argv[3] || 'linkedin';
  const trendId = process.argv[4] ? parseInt(process.argv[4]) : null;

  if (!topic) {
    console.log('Usage: node agents/copywriter.js "topik" [type] [trendId]');
    console.log('  type: linkedin | blog | email | landing-page');
    console.log('  trendId: optional, ID dari DB trending (auto-fetch artikel)');
    process.exit(1);
  }

  console.log(`[Copywriter] Nulis ${type} tentang: "${topic}"...\n`);
  
  generate(topic, type, trendId).then(result => {
    console.log('═'.repeat(50));
    console.log(result.body);
    console.log('═'.repeat(50));
    console.log(`\n${result.chars} karakter`);
    
    // Save ke DB
    const id = saveToDB(result);
    console.log(`\nLihat di: http://localhost:5000 (Drafts page)`);
  }).catch(e => {
    console.error('[Copywriter] Error:', e.message);
    process.exit(1);
  });
}

module.exports = { generate, saveToDB };
