/* copywrAIter — Frontend App */

let state = { page: 'dashboard', drafts: [], trends: [], posts: [], settings: {}, profile: {} };
const $ = id => document.getElementById(id);
const main = $('mainContent');

/* ── Routing ── */
function route(page) {
  state.page = page;
  document.querySelectorAll('.nav-item').forEach(el => el.classList.toggle('active', el.dataset.page === page));
  render();
  return false;
}

/* ── Render ── */
async function render() {
  const pages = {
    dashboard: renderDashboard,
    trends: renderTrends,
    drafts: renderDrafts,
    history: renderHistory,
    profile: renderProfile,
    settings: renderSettings
  };
  main.innerHTML = '<div class="loader"><div class="spinner"></div><p>Loading...</p></div>';
  try { await fetchData(); pages[state.page](); }
  catch(e) { main.innerHTML = '<div class="empty"><h2>Error</h2><p>' + e.message + '</p></div>'; }
}

async function fetchData() {
  const [s, t, d, h, p, st, ws] = await Promise.all([
    fetch('/api/status').then(r=>r.json()),
    fetch('/api/trends').then(r=>r.json()),
    fetch('/api/drafts').then(r=>r.json()),
    fetch('/api/history').then(r=>r.json()),
    fetch('/api/profile').then(r=>r.json()),
    fetch('/api/settings').then(r=>r.json()),
    fetch('/api/writing-style').then(r=>r.json()).catch(()=>({}))
  ]);
  state.status = s; state.trends = t.trends || [];
  state.drafts = d.drafts || []; state.posts = h.posts || [];
  state.profile = p.profile || {}; state.settings = st;
  state.writingStyle = ws.style || {};
  $('statusBadge').textContent = '● ' + (s.status || 'unknown');
  $('footerStats').textContent = state.drafts.length + ' drafts · ' + state.posts.length + ' posted';
}

/* ── Dashboard ── */
function renderDashboard() {
  const s = state.status?.stats || {};
  main.innerHTML = `
    <div class="stats-row">
      <div class="stat-card"><div class="stat-value">${s.trends||0}</div><div class="stat-label">Trends Today</div></div>
      <div class="stat-card"><div class="stat-value">${s.drafts||0}</div><div class="stat-label">Drafts</div></div>
      <div class="stat-card"><div class="stat-value">${s.posts||0}</div><div class="stat-label">Posted</div></div>
      <div class="stat-card"><div class="stat-value">${state.drafts.filter(d=>d.status==='scheduled').length}</div><div class="stat-label">Scheduled</div></div>
    </div>
    <div class="card">
      <div class="card-title">Recent Trends</div>
      ${state.trends.length === 0 ? '<div class="empty"><p>No trends yet. Run trend hunter to get started.</p></div>' :
        '<table><tr><th>Topic</th><th>Score</th><th>Source</th><th></th></tr>' +
        state.trends.slice(0,5).map(t => `<tr>
          <td>${esc(t.topic)}</td>
          <td>${t.score}</td>
          <td>${esc(t.source)}</td>
          <td>${t.source_url ? '<a href="'+escAttr(t.source_url)+'" target="_blank">Baca</a>' : ''} <a href="#" onclick="return generateDraft(${t.id},'${escAttr(t.topic)}')">Buat Draft</a></td>
        </tr>`).join('') + '</table>'
      }
    </div>
    <div class="card">
      <div class="card-title">Next Scheduled Post</div>
      ${scheduledDraft()}
    </div>
  `;
}

function scheduledDraft() {
  const next = state.drafts.filter(d => d.status === 'scheduled').sort((a,b) => a.scheduled_at?.localeCompare(b.scheduled_at))[0];
  if (!next) return '<div class="empty"><p>No scheduled posts.</p></div>';
  return `<div>${esc(next.topic || next.body?.substring(0,80))}</div><div style="color:var(--text2);font-size:.8rem">${next.scheduled_at}</div>`;
}

/* ── Trends ── */
function renderTrends() {
  main.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
      <h2>Trending Topics</h2>
      <button class="btn btn-primary btn-sm" onclick="return fetchTrends()">Refresh</button>
    </div>
    ${state.trends.length === 0 ? '<div class="empty"><h2>No Trends</h2><p>Click Refresh to fetch latest trends.</p></div>' :
      '<table><tr><th>Topic</th><th>Score</th><th>Source</th><th>Context</th><th></th></tr>' +
      state.trends.map(t => `<tr>
        <td><strong>${esc(t.topic)}</strong></td>
        <td><span class="tag">${t.score}</span></td>
        <td>${esc(t.source)}</td>
        <td style="font-size:.8rem;color:var(--text2);max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(t.context||'—')}</td>
        <td>${t.source_url ? '<a href="'+escAttr(t.source_url)+'" target="_blank">Baca</a>' : ''} <a href="#" onclick="return generateDraft(${t.id},'${escAttr(t.topic)}')">Buat Draft</a></td>
      </tr>`).join('') + '</table>'
    }
  `;
}

async function fetchTrends() {
  main.innerHTML = '<div class="loader"><div class="spinner"></div><p>Scraping trends...</p></div>';
  try {
    const r = await fetch('/api/trends/refresh', {method:'POST'});
    const d = await r.json();
    await fetchData();
    renderTrends();
  } catch(e) {
    main.innerHTML = `<div class="empty"><h2>Error</h2><p>${e.message}</p></div>`;
  }
}

/* ── Drafts ── */
let selectedDrafts = new Set();

function toggleDraftSelect(id) {
  if (selectedDrafts.has(id)) selectedDrafts.delete(id);
  else selectedDrafts.add(id);
  renderDrafts();
}

function toggleSelectAll() {
  const all = state.drafts.filter(d => d.status === 'draft' || d.status === 'approved');
  if (selectedDrafts.size === all.length) selectedDrafts.clear();
  else all.forEach(d => selectedDrafts.add(d.id));
  renderDrafts();
}

async function deleteSelectedDrafts() {
  if (selectedDrafts.size === 0) return;
  if (!confirm(`Hapus ${selectedDrafts.size} draft?`)) return;
  await fetch('/api/drafts/delete-batch', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body:JSON.stringify({ids: [...selectedDrafts]})
  });
  selectedDrafts.clear();
  await fetchData();
  renderDrafts();
}

async function deleteDraft(id) {
  if (!confirm('Hapus draft ini?')) return;
  await fetch('/api/draft/'+id, {method:'DELETE'});
  selectedDrafts.delete(id);
  await fetchData();
  renderDrafts();
}

function renderDrafts() {
  const grouped = {};
  ['draft','approved','scheduled','posted','rejected'].forEach(s => grouped[s] = state.drafts.filter(d => d.status === s));
  const selectable = state.drafts.filter(d => d.status === 'draft' || d.status === 'approved');
  const allSelected = selectable.length > 0 && selectedDrafts.size === selectable.length;
  main.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:8px">
      <h2>Drafts</h2>
      <div style="display:flex;gap:8px;align-items:center">
        ${selectable.length > 0 ? `
          <label style="font-size:.8rem;display:flex;align-items:center;gap:4px;cursor:pointer">
            <input type="checkbox" onchange="toggleSelectAll()" ${allSelected ? 'checked' : ''}> Select All
          </label>
          <button class="btn btn-sm btn-danger" onclick="deleteSelectedDrafts()" ${selectedDrafts.size === 0 ? 'disabled style="opacity:0.4"' : ''}>Hapus (${selectedDrafts.size})</button>
        ` : ''}
        <button class="btn btn-primary btn-sm" onclick="return showGenerateForm()">+ New Draft</button>
      </div>
    </div>
    ${['draft','approved','scheduled','posted','rejected'].map(s => `
      ${grouped[s].length === 0 ? '' : `
        <div class="card">
          <div class="card-title">${s.charAt(0).toUpperCase()+s.slice(1)} (${grouped[s].length})</div>
          <table>
            <tr><th>${s === 'draft' || s === 'approved' ? '<input type="checkbox">' : ''}</th><th>Topic</th><th>Preview</th><th>Score</th><th>Scheduled</th><th></th></tr>
            ${grouped[s].map(d => `<tr>
              ${s === 'draft' || s === 'approved' ? `<td><input type="checkbox" onchange="toggleDraftSelect(${d.id})" ${selectedDrafts.has(d.id) ? 'checked' : ''}></td>` : '<td></td>'}
              <td>${esc(d.topic||'—')}</td>
              <td><a href="#" onclick="return previewDraft(${d.id})" title="${escAttr(d.body?.substring(0,200))}">${esc(d.body?.substring(0,60))}...</a></td>
              <td><span class="tag">${d.score||'—'}</span></td>
              <td style="font-size:.75rem">${d.scheduled_at ? d.scheduled_at.substring(0,16) : '—'}</td>
              <td>${actionButtons(d)} <button class="btn btn-sm btn-danger" onclick="return deleteDraft(${d.id})" title="Hapus">✕</button></td>
            </tr>`).join('')}
          </table>
        </div>`
      }
    `).join('')}
    ${state.drafts.length === 0 ? '<div class="empty"><h2>No Drafts</h2><p>Generate your first draft from trending topics.</p></div>' : ''}
  `;
}

function actionButtons(d) {
  if (d.status === 'draft') return `<button class="btn btn-sm btn-success" onclick="return approveDraft(${d.id})">Approve</button> <button class="btn btn-sm btn-danger" onclick="return rejectDraft(${d.id})">Reject</button>`;
  if (d.status === 'approved') return `<button class="btn btn-sm" onclick="return scheduleDraft(${d.id})">Schedule</button> <button class="btn btn-sm btn-primary" onclick="return postNow(${d.id})">Post Now</button>`;
  if (d.status === 'rejected') return `<span style="color:var(--red);font-size:.75rem">Rejected</span>`;
  return `<span style="color:var(--text3);font-size:.75rem">${d.status}</span>`;
}

async function approveDraft(id) {
  await fetch('/api/draft/'+id+'/approve', {method:'POST'});
  await fetchData(); renderDrafts();
}
async function rejectDraft(id) {
  await fetch('/api/draft/'+id+'/reject', {method:'POST'});
  await fetchData(); renderDrafts();
}
async function postNow(id) {
  if (!confirm('Post this draft now?')) return;
  await fetch('/api/post/now', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({draft_id:id})});
  await fetchData(); renderDrafts();
}

function showGenerateForm() {
  main.innerHTML = `
    <div class="card">
      <div class="card-title">Generate New Draft</div>
      <div class="form-group">
        <label class="form-label">Topic / Trend</label>
        <input type="text" id="draftTopic" placeholder="e.g. AI Automation 2026" value="${state.trends[0]?.topic||''}">
      </div>
      <div class="form-group">
        <label class="form-label">Tone</label>
        <select id="draftTone"><option value="professional-santai">Professional Santai</option><option value="thought-leadership">Thought Leadership</option><option value="storytelling">Storytelling</option></select>
      </div>
      <div style="display:flex;gap:8px;margin-bottom:12px">
        <button class="btn btn-primary" onclick="return generateAIDraft()">✨ Generate with AI</button>
        <span style="color:var(--text3);font-size:.8rem;align-self:center">or write manually below</span>
      </div>
      <div class="form-group">
        <label class="form-label">Manual Draft Body</label>
        <textarea id="draftBody" placeholder="Write draft content manually..."></textarea>
      </div>
      <div class="form-group">
        <label class="form-label">Hashtags</label>
        <input type="text" id="draftHashtags" placeholder="#AI #Automation">
      </div>
      <button class="btn" onclick="return saveDraft()">Save Draft</button>
    </div>
  `;
}

async function generateAIDraft() {
  const topic = $('draftTopic').value;
  const tone = $('draftTone').value;
  main.innerHTML = '<div class="loader"><div class="spinner"></div><p>Membaca berita & nulis draft...</p></div>';
  try {
    const r = await fetch('/api/draft/generate-ai', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({topic, tone})
    });
    const d = await r.json();
    if (!r.ok) throw new Error(d.error || 'Gagal');
    await fetchData();
    previewDraft(d.id);
  } catch(e) {
    main.innerHTML = `<div class="empty"><h2>Error</h2><p>${e.message}</p></div>`;
  }
}

async function saveDraft() {
  const body = $('draftBody').value;
  if (!body) { alert('Write something'); return; }
  await fetch('/api/draft/generate', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body:JSON.stringify({body, hashtags:$('draftHashtags').value, topic_id:null})
  });
  await fetchData(); route('drafts');
}

/* ── History ── */
function renderHistory() {
  main.innerHTML = `
    <h2 style="margin-bottom:12px">Post History</h2>
    ${state.posts.length === 0 ? '<div class="empty"><h2>No Posts Yet</h2><p>Posts will appear here after publishing.</p></div>' :
      '<table><tr><th>Date</th><th>Content</th><th>Likes</th><th>Comments</th><th>Shares</th><th>Views</th></tr>' +
      state.posts.map(p => `<tr>
        <td style="font-size:.75rem">${p.posted_at?.substring(0,10)||'—'}</td>
        <td>${esc(p.draft_body?.substring(0,80))}...</td>
        <td>${p.likes||0}</td>
        <td>${p.comments||0}</td>
        <td>${p.shares||0}</td>
        <td>${p.views||0}</td>
      </tr>`).join('') + '</table>'
    }
  `;
}

/* ── Profile ── */
function renderProfile() {
  const p = state.profile;
  main.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
      <h2>LinkedIn Profile</h2>
      <button class="btn btn-sm btn-primary" onclick="return generateSuggestions()">Generate Suggestions</button>
      <button class="btn btn-sm" onclick="return loadSuggestions()">Lihat Tersimpan</button>
    </div>
    <div class="card">
      <div class="card-title">${esc(p.personal_info?.display_name||'Name not set')}</div>
      <div style="color:var(--text2)">${esc(p.personal_info?.headline||'')}</div>
      <div style="color:var(--text3);font-size:.8rem;margin-top:4px">${esc(p.personal_info?.location||'')}</div>
    </div>
    <div class="card">
      <div class="card-title">About</div>
      <p style="color:var(--text2);font-size:.85rem">${esc(p.about?.current||p.about?.goal||'Not set. Edit in knowledge_base/profile.json')}</p>
    </div>
    <div class="card">
      <div class="card-title">Experience (${(p.experience||[]).length})</div>
      ${(p.experience||[]).length === 0 ? '<div style="color:var(--text3)">No experience listed.</div>' :
        (p.experience||[]).map(e => `<div style="margin-bottom:8px"><strong>${esc(e.title)}</strong> @ ${esc(e.company)} <span style="color:var(--text3);font-size:.75rem">${e.start_date||''} — ${e.end_date||''}</span></div>`).join('')}
    </div>
    <div class="card">
      <div class="card-title">Skills</div>
      ${(p.skills||[]).map(s => `<span class="tag">${esc(s)}</span>`).join(' ') || '<span style="color:var(--text3)">No skills listed.</span>'}
    </div>
  `;
}

async function generateSuggestions() {
  main.innerHTML = '<div class="loader"><div class="spinner"></div><p>Menganalisis profil & menghasilkan saran...</p></div>';
  try {
    const r = await fetch('/api/profile/optimize', { method: 'POST' });
    const d = await r.json();
    if (d.error) throw new Error(d.error);
    await loadSuggestions();
  } catch(e) {
    main.innerHTML = `<div class="empty"><h2>Error</h2><p>${e.message}</p></div>`;
  }
}

async function loadSuggestions() {
  main.innerHTML = '<div class="loader"><div class="spinner"></div><p>Analyzing profile...</p></div>';
  try {
    const r = await fetch('/api/profile/suggestions');
    const d = await r.json();
    const suggestions = d.suggestions || [];
    main.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
        <h2>Profile Suggestions</h2>
        <button class="btn btn-sm btn-primary" onclick="return generateSuggestions()">Generate Baru</button>
        <button class="btn btn-sm" onclick="return route('profile')">Back</button>
      </div>
      ${suggestions.length === 0 ? '<div class="empty"><h2>No Suggestions</h2><p>AI optimization coming soon.</p></div>' :
        suggestions.map(s => `
          <div class="card">
            <div style="color:var(--text2);font-size:.75rem;text-transform:uppercase;margin-bottom:4px">${esc(s.field)} — <span class="status-${s.status}">${s.status}</span></div>
            ${s.old_text ? `<div style="margin:8px 0;padding:8px;background:var(--bg);border-radius:var(--radius);opacity:.6">
              <div style="font-size:.75rem;color:var(--text3)">Saat ini:</div>
              ${esc(s.old_text)}
            </div>` : ''}
            <div style="margin:8px 0;padding:8px;background:var(--bg2);border-radius:var(--radius)">
              <div style="font-size:.75rem;color:var(--green)">Saran:</div>
              ${esc(s.new_text)}
            </div>
            <div style="font-size:.8rem;color:var(--text2)">${esc(s.reason)}</div>
            ${s.status === 'pending' ? `<div style="margin-top:8px;display:flex;gap:8px">
              <button class="btn btn-sm btn-success" onclick="return approveSuggestion(${s.id})">Approve</button>
              <button class="btn btn-sm" onclick="return rejectSuggestion(${s.id})">Tolak</button>
            </div>` : ''}
          </div>
        `).join('')
      }
    `;
  } catch(e) {
    main.innerHTML = `<div class="empty"><h2>Error</h2><p>${e.message}</p></div>`;
  }
}

async function approveSuggestion(id) {
  await fetch('/api/profile/suggestion/'+id+'/approve', {method:'POST'});
  await loadSuggestions();
}

async function rejectSuggestion(id) {
  await fetch('/api/profile/suggestion/'+id+'/reject', {method:'POST'});
  await loadSuggestions();
}

/* ── Settings ── */
function renderSettings() {
  main.innerHTML = `
    <h2 style="margin-bottom:12px">Settings</h2>
    <div class="card">
      <div class="card-title">LinkedIn Connection</div>
      <div id="linkedinStatus">Checking...</div>
      <div style="margin-top:8px">
        <button class="btn btn-primary btn-sm" onclick="return connectLinkedIn()">Connect LinkedIn</button>
        <button class="btn btn-sm" onclick="return checkLinkedIn()">Refresh Status</button>
      </div>
    </div>
    <div class="card">
      <div class="card-title">Writing Style (JSON — edit langsung)</div>
      <div style="font-size:.75rem;color:var(--text3);margin-bottom:8px">Edit seluruh konfigurasi writing style. Format JSON. Hati-hati dengan koma dan tanda kutip.</div>
      <div class="form-group">
        <textarea id="wsFull" rows="25" style="font-family:monospace;font-size:.8rem;white-space:pre;overflow:auto">${JSON.stringify(state.writingStyle, null, 2) || '{}'}</textarea>
      </div>
      <div style="display:flex;gap:8px">
        <button class="btn btn-primary btn-sm" onclick="return saveWritingStyle()">Save Style</button>
        <button class="btn btn-sm" onclick="return resetWritingStyle()">Reset Default</button>
        <span id="wsStatus" style="font-size:.75rem;color:var(--green);align-self:center"></span>
      </div>
    </div>
      <div class="form-group"><label class="form-label">Tone</label><input type="text" id="sTone" value="${state.settings.tone||'professional-santai'}"></div>
      <div class="form-group"><label class="form-label">Posting Times (comma-separated, 24h)</label><input type="text" id="sTimes" value="${state.settings.post_times||'07:00,19:00'}"></div>
      <div class="form-group"><label class="form-label">Max Posts / Day</label><input type="number" id="sMax" value="${state.settings.max_posts||'2'}"></div>
      <button class="btn btn-primary" onclick="return saveSettings()">Save</button>
    </div>
    <div class="card">
      <div class="card-title">Knowledge Base</div>
      <div style="font-size:.85rem;color:var(--text2)">
        <p>Edit files directly in <code>knowledge_base/</code>:</p>
        <ul style="margin:8px 0 0 16px">
          <li><code>profile.json</code> — your LinkedIn data</li>
          <li><code>brand_voice.json</code> — tone, style, hashtags</li>
          <li><code>content_calendar.json</code> — schedule config</li>
        </ul>
      </div>
    </div>
  `;
}

async function saveSettings() {
  const data = {
    tone: $('sTone').value,
    post_times: $('sTimes').value,
    max_posts: $('sMax').value
  };
  await fetch('/api/settings', {method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
  // Save writing style from JSON textarea
  const wsEl = $('wsFull');
  if (wsEl) {
    try {
      const ws = JSON.parse(wsEl.value);
      await fetch('/api/writing-style', {method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(ws)});
      const statusEl = $('wsStatus');
      if (statusEl) statusEl.textContent = '✓ Saved at ' + new Date().toLocaleTimeString();
    } catch(e) {
      alert('JSON tidak valid: ' + e.message);
      return;
    }
  }
  await fetchData();
  alert('Settings & Writing Style saved');
}

async function resetWritingStyle() {
  if (!confirm('Reset writing style ke default?')) return;
  await fetch('/api/writing-style/reset', {method:'POST'});
  await fetchData();
  route('settings');
}

async function checkLinkedIn() {
  const r = await fetch('/api/linkedin/status');
  const d = await r.json();
  const el = $('linkedinStatus');
  if (d.linked) {
    el.innerHTML = `<span style="color:var(--green)">✓ Connected</span> — URN: ${d.profile_urn || 'unknown'} ${d.expired ? '<span style="color:var(--red)">(token expired - reconnect)</span>' : ''}`;
  } else {
    el.innerHTML = '<span style="color:var(--text3)">✗ Not connected</span>';
  }
}

async function connectLinkedIn() {
  const r = await fetch('/api/linkedin/login');
  const d = await r.json();
  if (d.error) {
    alert('LinkedIn not configured: ' + d.error + '\n\nSetup: ' + d.setup_url);
  } else {
    // Should redirect
    window.location.href = '/api/linkedin/login';
  }
}

/* ── Draft Preview ── */
function previewDraft(id) {
  const draft = state.drafts.find(d => d.id === id);
  if (!draft) return;
  // Find related trend for source article link
  const trend = state.trends.find(t => draft.topic_id === t.id || (draft.topic && t.topic && draft.topic.includes(t.topic.substring(0,30))));
  const sourceInfo = trend?.source_url ? `<div style="margin-top:16px;padding:12px;background:var(--bg2);border-radius:var(--radius);font-size:.8rem;color:var(--text2)">
    <strong>Sumber:</strong> <a href="${escAttr(trend.source_url)}" target="_blank">${esc(trend.source)} — ${esc(trend.topic)}</a>
  </div>` : '';
  main.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
      <h2>${esc(draft.topic || 'Draft')}</h2>
      <button class="btn btn-sm" onclick="return renderDrafts()">Back</button>
    </div>
    <div class="card">
      <div style="display:flex;gap:12px;margin-bottom:12px;flex-wrap:wrap">
        <span class="tag status-${draft.status}">${draft.status}</span>
        <span class="tag">Score: ${draft.score||'—'}</span>
        ${draft.scheduled_at ? `<span class="tag">Scheduled: ${draft.scheduled_at.substring(0,16)}</span>` : ''}
      </div>
      <div style="white-space:pre-wrap;font-size:.9rem;line-height:1.8;background:var(--bg);padding:16px;border-radius:var(--radius);border:1px solid var(--border)">
${esc(draft.body)}
      </div>
      <div style="margin-top:12px;color:var(--text2);font-size:.85rem">
        ${esc(draft.hashtags || '')}
      </div>
      <div style="margin-top:16px;display:flex;gap:8px">
        ${actionButtons(draft)}
      </div>
      ${sourceInfo || ''}
    </div>
  `;
}

/* ── Actions from Trends ── */
async function generateDraft(topicId, topicName) {
  main.innerHTML = '<div class="loader"><div class="spinner"></div><p>Membaca artikel...</p></div>';
  try {
    const r = await fetch('/api/draft/generate-ai', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({topic_id:topicId, topic:topicName})
    });
    const d = await r.json();
    if (!r.ok) throw new Error(d.error || 'Gagal generate');
    await fetchData();
    // Show preview immediately
    previewDraft(d.id);
  } catch(e) {
    main.innerHTML = `<div class="empty"><h2>Error</h2><p>${e.message}</p></div>`;
  }
}

/* ── Schedule ── */
async function scheduleDraft(id) {
  const date = prompt('Schedule date/time (YYYY-MM-DDTHH:MM):');
  if (!date) return;
  await fetch('/api/draft/'+id+'/schedule', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body:JSON.stringify({scheduled_at: date})
  });
  await fetchData(); renderDrafts();
}

/* ── Escape ── */
function esc(s) { if (!s) return ''; const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }
function escAttr(s) { return (s||'').replace(/'/g,"\\'").replace(/"/g,'&quot;'); }

/* ── Init ── */
document.addEventListener('DOMContentLoaded', () => render());
