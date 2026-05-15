#!/usr/bin/env node
// copywrAIter — Agents Entry Point
// 
// Agents:
//   research.js    — Trend research & enrichment
//   copywriter.js  — AI copywriting (warkop tone)
//   publisher.js   — Publish ke social media
//   run.js         — Orchestrator (full flow)
//
// Usage:
//   node agents/research.js [limit]
//   node agents/copywriter.js "topik" [type] [trendId]
//   node agents/publisher.js <draftId> [platform] [--repliz]
//   node agents/run.js [--publish] [--limit 3]

const { research } = require('./research.js');
const { generate, saveToDB } = require('./copywriter.js');
const { publish } = require('./publisher.js');

console.log('copywrAIter Agents — CLI Tools');
console.log('');
console.log('  node agents/research.js [limit]         — Research trending topik');
console.log('  node agents/copywriter.js "topik" ...   — Generate copywriting');
console.log('  node agents/publisher.js <draftId> ...  — Publish ke social media');
console.log('  node agents/run.js [--publish]          — Full flow otomatis');
console.log('');
console.log('Contoh:');
console.log('  SUMOPOD_API_KEY=xxx node agents/research.js 3');
console.log('  SUMOPOD_API_KEY=xxx node agents/copywriter.js "AI tools mahal" linkedin');
console.log('  node agents/run.js --limit 2');

module.exports = { research, generate, saveToDB, publish };
