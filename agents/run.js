#!/usr/bin/env node
// copywrAIter — Orchestrator Agent
// Full flow: Research → Copywrite → Publish
// CLI: node agents/run.js [--publish] [--platform linkedin] [--limit 3]

const { research } = require('./research.js');
const { generate, saveToDB } = require('./copywriter.js');
const { publish } = require('./publisher.js');

async function run() {
  const args = process.argv.slice(2);
  const doPublish = args.includes('--publish');
  const platform = args.includes('--platform') ? args[args.indexOf('--platform') + 1] : 'linkedin';
  const limit = args.includes('--limit') ? parseInt(args[args.indexOf('--limit') + 1]) : 3;
  const useRepliz = args.includes('--repliz');

  console.log('╔════════════════════════════════════════╗');
  console.log('║    copywrAIter — Autonomous Agent      ║');
  console.log('╚════════════════════════════════════════╝\n');

  // ── PHASE 1: Research ──
  console.log('▸ PHASE 1: Research trending topics\n');
  const topics = await research(limit);
  if (topics.length === 0) {
    console.log('Tidak ada topik. Jalankan trend hunter dulu via Dashboard.');
    process.exit(0);
  }

  // ── PHASE 2: Generate copy ──
  console.log('\n▸ PHASE 2: Generate copywriting\n');
  const drafts = [];
  for (const t of topics) {
    process.stdout.write(`  Nulis "${t.topic.substring(0, 50)}"... `);
    try {
      const result = await generate(t.topic, platform, t.id);
      saveToDB(result);
      drafts.push(result);
      console.log(`✅ ${result.chars} karakter`);
    } catch(e) {
      console.log(`❌ ${e.message}`);
    }
  }

  console.log(`\n${drafts.length} draft tersimpan! Lihat di http://localhost:5000`);

  // ── PHASE 3: Publish (opsional) ──
  if (doPublish && drafts.length > 0) {
    console.log(`\n▸ PHASE 3: Publish ke ${platform}\n`);
    for (const d of drafts) {
      process.stdout.write(`  Publish "${d.topic.substring(0, 50)}"... `);
      try {
        await publish(d.id, platform, useRepliz);
        console.log('✅');
      } catch(e) {
        console.log(`❌ ${e.message}`);
      }
    }
  }

  console.log('\n╔════════════════════════════════════════╗');
  console.log('║    Selesai! 🎉                        ║');
  console.log('╚════════════════════════════════════════╝');
}

run().catch(e => {
  console.error('\n[Run] Fatal:', e.message);
  process.exit(1);
});
