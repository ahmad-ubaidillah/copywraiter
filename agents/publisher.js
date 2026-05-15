// copywrAIter — Publisher Agent
// Publish copy ke social media via Repliz API (atau LinkedIn langsung)
// CLI: node agents/publisher.js <draftId> [platform]
//
// Repliz API: butuh akun Standard+ (Rp18k/bulan)
// Daftar: https://repliz.com
// API key akan dikasih pas login

const API_KEY = process.env.SUMOPOD_API_KEY || '';
const REPLIZ_API_KEY = process.env.REPLIZ_API_KEY || '';
const REPLIZ_BASE = 'https://api.repliz.com/v1'; // placeholder
const DB_PATH = __dirname + '/../data/app.db';

const Database = require('better-sqlite3');
const fs = require('fs');

// ── Ambil draft dari DB ──
function getDraft(id) {
  const db = new Database(DB_PATH);
  const row = db.prepare("SELECT * FROM drafts WHERE id=?").get(id);
  db.close();
  return row;
}

// ── Update status draft ──
function updateDraftStatus(id, status, platform) {
  const db = new Database(DB_PATH);
  db.prepare("UPDATE drafts SET status=?, humanized_from=? WHERE id=?").run(status, platform, id);
  db.close();
}

// ── Save ke tabel posts ──
function savePost(draftId, platform, postUrl, status) {
  const db = new Database(DB_PATH);
  db.prepare(
    "INSERT INTO posts (draft_id, platform, post_url, status, created_at) VALUES (?,?,?,?,datetime('now'))"
  ).run(draftId, platform, postUrl || '', status);
  db.close();
}

// ── Publish via Repliz API ──
async function publishViaRepliz(body, platform = 'linkedin') {
  if (!REPLIZ_API_KEY) {
    throw new Error('REPLIZ_API_KEY belum diset. Daftar di https://repliz.com');
  }

  // Repliz API endpoint — sesuaikan dengan dokumentasi resmi mereka
  const platformMap = {
    linkedin: 'linkedin',
    facebook: 'facebook',
    instagram: 'instagram',
    twitter: 'twitter',
    tiktok: 'tiktok'
  };

  const target = platformMap[platform] || platform;

  const resp = await fetch(REPLIZ_BASE + '/posts', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer ' + REPLIZ_API_KEY,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      platform: target,
      content: body,
      schedule: null // langsung publish
    })
  });

  if (!resp.ok) {
    const err = await resp.text();
    throw new Error('Repliz API: ' + (err || resp.statusText));
  }

  return await resp.json();
}

// ── Publish langsung ke LinkedIn (fallback, butuh token) ──
async function publishViaLinkedIn(body, accessToken) {
  if (!accessToken) {
    accessToken = process.env.LINKEDIN_ACCESS_TOKEN;
  }
  if (!accessToken) {
    throw new Error('LINKEDIN_ACCESS_TOKEN tidak diset. Hubungkan LinkedIn dulu di Settings.');
  }

  // Dapetin profile URN dari DB
  const db = new Database(DB_PATH);
  const tokenRow = db.prepare("SELECT * FROM linkedin_tokens ORDER BY id DESC LIMIT 1").get();
  db.close();

  if (!tokenRow || !tokenRow.profile_urn) {
    throw new Error('LinkedIn belum terhubung. Klik "Connect LinkedIn" di Settings.');
  }

  const resp = await fetch('https://api.linkedin.com/rest/posts', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer ' + accessToken,
      'Content-Type': 'application/json',
      'LinkedIn-Version': '202501',
      'X-Restli-Protocol-Version': '2.0.0'
    },
    body: JSON.stringify({
      author: tokenRow.profile_urn,
      lifecycleState: 'PUBLISHED',
      visibility: 'PUBLIC',
      commentary: body
    })
  });

  if (!resp.ok) {
    const err = await resp.text();
    throw new Error('LinkedIn API: ' + (err || resp.statusText));
  }

  return await resp.json();
}

// ── Main publish ──
async function publish(draftId, platform = 'linkedin', useRepliz = false) {
  console.log(`[Publisher] Mempublikasikan draft #${draftId} ke ${platform}...`);

  const draft = getDraft(draftId);
  if (!draft) {
    console.error(`[Publisher] Draft #${draftId} tidak ditemukan`);
    process.exit(1);
  }
  if (draft.status === 'posted') {
    console.error(`[Publisher] Draft #${draftId} sudah dipublikasikan`);
    process.exit(1);
  }

  console.log(`  Topic: ${draft.topic}`);
  console.log(`  Body: ${draft.body?.substring(0, 80)}...\n`);

  let result;
  try {
    if (useRepliz && REPLIZ_API_KEY) {
      result = await publishViaRepliz(draft.body, platform);
      console.log(`[Publisher] ✅ Dipublikasikan via Repliz: ${result.post_url || '(cek dashboard Repliz)'}`);
    } else {
      result = await publishViaLinkedIn(draft.body);
      console.log(`[Publisher] ✅ Dipublikasikan ke LinkedIn`);
    }

    updateDraftStatus(draftId, 'posted', platform);
    savePost(draftId, platform, result?.post_url || result?.id || '', 'published');
    
    console.log(`[Publisher] Selesai. Draft #${draftId} → posted`);
    return result;
  } catch(e) {
    console.error(`[Publisher] ❌ Gagal: ${e.message}`);
    updateDraftStatus(draftId, 'publish_failed', platform);
    savePost(draftId, platform, '', 'failed');
    process.exit(1);
  }
}

// ── CLI ──
if (require.main === module) {
  const draftId = parseInt(process.argv[2]);
  const platform = process.argv[3] || 'linkedin';
  const useRepliz = process.argv.includes('--repliz');

  if (!draftId) {
    console.log('Usage: node agents/publisher.js <draftId> [platform] [--repliz]');
    console.log('  draftId: ID draft di DB');
    console.log('  platform: linkedin (default) | facebook | instagram | twitter | tiktok');
    console.log('  --repliz: pake Repliz API (butuh key)');
    console.log('');
    console.log('Env:');
    console.log('  LINKEDIN_ACCESS_TOKEN — LinkedIn OAuth token');
    console.log('  REPLIZ_API_KEY — Repliz API key (dari repliz.com)');
    process.exit(1);
  }

  publish(draftId, platform, useRepliz);
}

module.exports = { publish, publishViaRepliz, publishViaLinkedIn };