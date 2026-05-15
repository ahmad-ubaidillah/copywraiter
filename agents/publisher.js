// copywrAIter — Publisher Agent
// Publish copy ke social media via Repliz API (atau LinkedIn langsung)
// CLI: node agents/publisher.js <draftId> [platform]
//
// Repliz API (repliz.com):
//   - Basic Auth: access-key:secret-key
//   - Content management endpoint (butuh Standard plan, Rp18k/bulan)
//   - Saat ini: cuma account yang bisa diakses (Free plan)

const REPLIZ_ACCESS_KEY = process.env.REPLIZ_ACCESS_KEY || '9221167021';
const REPLIZ_SECRET_KEY = process.env.REPLIZ_SECRET_KEY || 'c1nNqv947lfwBtMyelNrY9MgKu7npDG2';
const REPLIZ_BASE = 'https://api.repliz.com/public';
const DB_PATH = __dirname + '/../data/app.db';

const Database = require('better-sqlite3');
const fs = require('fs');

// ── Get connected accounts from Repliz ──
async function getConnectedAccounts() {
  const resp = await fetch(REPLIZ_BASE + '/account?page=1&limit=20', {
    headers: {
      'Authorization': 'Basic ' + Buffer.from(REPLIZ_ACCESS_KEY + ':' + REPLIZ_SECRET_KEY).toString('base64')
    }
  });
  if (!resp.ok) throw new Error('Repliz: ' + resp.statusText);
  const data = await resp.json();
  return data.docs || [];
}

// ── Publish via Repliz (read-only API — posting via web UI) ──
async function publishViaRepliz(body, platform = 'threads') {
  const accounts = await getConnectedAccounts();
  const account = accounts.find(a => a.type === platform);
  if (!account) {
    throw new Error(`Tidak ada akun ${platform} terhubung di Repliz. Punya: ${accounts.map(a=>a.type+'/'+a.username).join(', ') || 'tidak ada'}`);
  }

  // Repliz API saat ini hanya read-only untuk Free plan.
  // Content management butuh Standard plan (Rp18k/bulan).
  // Untuk ngepost, buka web UI: https://repliz.com
  
  // Coba POST — kalo gagal, kasih tahu cara manual
  const resp = await fetch(REPLIZ_BASE + '/content', {
    method: 'POST',
    headers: {
      'Authorization': 'Basic ' + Buffer.from(REPLIZ_ACCESS_KEY + ':' + REPLIZ_SECRET_KEY).toString('base64'),
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      account_id: account._id,
      platform: platform,
      title: 'copywrAIter post',
      content: body,
      image_url: ''
    })
  });

  if (resp.status === 402 || resp.status === 404 || !resp.ok) {
    const err = await resp.json().catch(() => ({}));
    // API write belum available — kasih petunjuk manual
    const postNote = `
╔════════════════════════════════════════════════╗
║  Repliz API saat ini read-only (Free plan).   ║
║  Untuk posting, buka langsung:                ║
║                                                ║
║  🌐 https://repliz.com                        ║
║                                                ║
║  Atau upgrade ke Standard (Rp18k/bulan)       ║
║  untuk akses Content API.                     ║
╚════════════════════════════════════════════════╝`;
    throw new Error(postNote);
  }

  return await resp.json();
}

// ── Publish via LinkedIn (fallback) ──
async function publishViaLinkedIn(body, accessToken) {
  if (!accessToken) {
    accessToken = process.env.LINKEDIN_ACCESS_TOKEN;
  }
  if (!accessToken) {
    throw new Error('LINKEDIN_ACCESS_TOKEN tidak diset.');
  }

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

// ── Ambil draft dari DB ──
function getDraft(id) {
  const db = new Database(DB_PATH);
  const row = db.prepare("SELECT d.*, t.topic FROM drafts d LEFT JOIN trends t ON d.topic_id = t.id WHERE d.id=?").get(id);
  db.close();
  return row;
}

function updateDraftStatus(id, status, platform) {
  const db = new Database(DB_PATH);
  try {
    db.prepare("UPDATE drafts SET status=? WHERE id=?").run(status, id);
  } catch(e) {
    // column mungkin beda, skip
  }
  db.close();
}

function savePost(draftId, platform, postUrl, status) {
  const db = new Database(DB_PATH);
  try {
    db.prepare(
      "INSERT INTO posts (draft_id, platform, post_url, posted_at) VALUES (?,?,?,datetime('now'))"
    ).run(draftId, platform, postUrl || '');
  } catch(e) {
    // column mungkin beda
  }
  db.close();
}

// ── Main publish ──
async function publish(draftId, platform = 'linkedin', useRepliz = false) {
  console.log(`[Publisher] Mempublikasikan draft #${draftId} ke ${platform}...\n`);

  const draft = getDraft(draftId);
  if (!draft) {
    console.error(`[Publisher] Draft #${draftId} tidak ditemukan`);
    process.exit(1);
  }
  if (draft.status === 'posted') {
    console.error(`[Publisher] Draft #${draftId} sudah dipublikasikan`);
    process.exit(1);
  }

  console.log(`  Topik: ${draft.topic || '(tanpa topik)'}`);
  console.log(`  Body: ${(draft.body || '').substring(0, 100)}...\n`);

  let result;
  try {
    if (useRepliz) {
      // Cek akun yang connect
      const accounts = await getConnectedAccounts();
      console.log(`  Akun Repliz terhubung:`);
      for (const a of accounts) {
        console.log(`    - ${a.type}/${a.username} (${a.isConnected ? '✅' : '❌'})`);
      }
      console.log();

      // Coba publish
      result = await publishViaRepliz(draft.body, platform);
      const postUrl = result?.post_url || result?._id || '';
      console.log(`[Publisher] ✅ Dipublikasikan via Repliz: ${postUrl ? postUrl : '(cek dashboard repliz.com)'}`);
    } else {
      result = await publishViaLinkedIn(draft.body);
      console.log(`[Publisher] ✅ Dipublikasikan ke LinkedIn`);
    }

    updateDraftStatus(draftId, 'posted', platform);
    savePost(draftId, platform, result?.post_url || result?.id || '', 'published');
    console.log(`\n[Publisher] Selesai. Draft #${draftId} → posted`);
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
    console.log('');
    console.log('  draftId:  ID draft di DB');
    console.log('  platform: linkedin (default) | threads | instagram | facebook | tiktok');
    console.log('  --repliz: pake Repliz API (butuh Standard plan Rp18k/bulan)');
    console.log('');
    console.log('Env:');
    console.log('  LINKEDIN_ACCESS_TOKEN — LinkedIn OAuth token');
    console.log('  REPLIZ_ACCESS_KEY — Repliz access key');
    console.log('  REPLIZ_SECRET_KEY — Repliz secret key');
    process.exit(1);
  }

  publish(draftId, platform, useRepliz);
}

module.exports = { publish, publishViaRepliz, publishViaLinkedIn, getConnectedAccounts };
