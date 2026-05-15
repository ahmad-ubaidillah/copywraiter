// copywrAIter — Research Agent
// Baca trending dari DB, kategorisasi, enrichment pake AI
// CLI: node agents/research.js [limit]

const API_KEY = process.env.SUMOPOD_API_KEY || process.env.OPENAI_API_KEY || '';
const BASE_URL = process.env.OPENAI_BASE_URL || 'https://ai.sumopod.com/v1';
const MODEL = process.env.OPENAI_MODEL || 'qwen3.6-plus';
const DB_PATH = __dirname + '/../data/app.db';

const Database = require('better-sqlite3');
const fs = require('fs');

// ── Baca trending dari DB ──
function getTrendingFromDB(limit = 20) {
  const db = new Database(DB_PATH);
  const rows = db.prepare("SELECT * FROM trends ORDER BY score DESC LIMIT ?").all(limit);
  db.close();
  return rows;
}

// ── Enrich 1 topik pake AI ──
async function enrichTopic(topic) {
  if (!API_KEY) return { topic, category: 'general', virality: 50 };

  const prompt = `Analisis topik ini: "${topic}"

Berikan JSON:
{
  "category": "technology | economy | lifestyle | entertainment | politics | general",
  "virality": 0-100,
  "hook_angle": "kalimat hook warkop kasar untuk LinkedIn",
  "audience": "target audiens yang peduli topik ini"
}
Hanya JSON, tanpa markdown.`;

  try {
    const resp = await fetch(BASE_URL + '/chat/completions', {
      method: 'POST',
      headers: { 'Authorization': 'Bearer ' + API_KEY, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: MODEL,
        messages: [
          { role: 'system', content: 'Kamu analis topik viral Indonesia. Output JSON.' },
          { role: 'user', content: prompt }
        ],
        temperature: 0.3,
        max_tokens: 256
      })
    });
    const data = await resp.json();
    const text = (data.choices?.[0]?.message?.content || '{}')
      .replace(/```json|```/g, '').trim();
    const parsed = JSON.parse(text);
    return { topic, ...parsed };
  } catch(e) {
    return { topic, category: 'general', virality: 50, hook_angle: '', audience: '' };
  }
}

// ── Research pipeline ──
async function research(limit = 5) {
  console.log('[Research] Mulai research trending topik...\n');
  
  const trends = getTrendingFromDB(20);
  const top = trends.slice(0, Math.min(limit, trends.length));
  
  if (top.length === 0) {
    console.log('[Research] Tidak ada trending. Jalankan trend hunter dulu.');
    return [];
  }

  console.log(`[Research] ${top.length} topik dari DB, enrichment...\n`);

  const enriched = [];
  for (const t of top) {
    process.stdout.write(`  → ${t.topic}... `);
    const en = await enrichTopic(t.topic);
    enriched.push({
      id: t.id,
      topic: t.topic,
      source: t.source,
      score: t.score,
      url: t.source_url,
      category: en.category,
      virality: en.virality,
      hook_angle: en.hook_angle,
      audience: en.audience
    });
    console.log(`${en.category} (viral: ${en.virality})`);
  }

  // Group by category
  const grouped = {};
  for (const e of enriched) {
    const c = e.category || 'general';
    if (!grouped[c]) grouped[c] = [];
    grouped[c].push(e);
  }

  console.log('\n[Research] Ringkasan:');
  for (const [cat, items] of Object.entries(grouped)) {
    console.log(`  ${cat}: ${items.length} topik`);
    for (const i of items) console.log(`    - ${i.topic} [${i.virality}]`);
  }

  // Save
  const outdir = __dirname + '/../data/research';
  fs.mkdirSync(outdir, { recursive: true });
  fs.writeFileSync(outdir + '/latest.json', JSON.stringify(enriched, null, 2));
  fs.writeFileSync(outdir + '/latest-summary.txt',
    enriched.map(e => `${e.virality}|${e.category}|${e.topic}|${e.hook_angle}`).join('\n')
  );
  
  console.log(`\n[Research] Selesai. ${enriched.length} topik → data/research/latest.json`);
  return enriched;
}

// ── CLI ──
if (require.main === module) {
  const limit = parseInt(process.argv[2] || '5');
  research(limit).catch(e => {
    console.error('[Research] Error:', e.message);
    process.exit(1);
  });
}

module.exports = { research, getTrendingFromDB, enrichTopic };
