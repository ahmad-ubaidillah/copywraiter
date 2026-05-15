// copywrAIter Agent Scripts

// Trend Hunter — scrape trending topics from Trends24 + Google Trends
async function scrapeTrends24() {
  const resp = await fetch('https://trends24.in/indonesia/');
  const html = await resp.text();
  // Parse trending topics from Trends24 HTML
  const topics = [];
  const regex = /<a[^>]*href="[^"]*"[^>]*class="[^"]*"[^>]*>([^<]+)<\/a>/g;
  let match;
  while ((match = regex.exec(html)) !== null) {
    const text = match[1].trim();
    if (text && !text.startsWith('#') && text.length > 3 && text.length < 60) {
      topics.push({ topic: text, source: 'trends24', score: 50 });
    }
  }
  return topics.slice(0, 30);
}

async function scrapeGoogleTrends() {
  const resp = await fetch('https://trends.google.com/trending?geo=ID&sort=trending', {
    headers: { 'User-Agent': 'Mozilla/5.0' }
  });
  const html = await resp.text();
  const topics = [];
  const regex = /<div[^>]*class="[^"]*title"[^>]*>([^<]+)<\/div>/g;
  let match;
  while ((match = regex.exec(html)) !== null) {
    topics.push({ topic: match[1].trim(), source: 'google_trends', score: 60 });
  }
  return topics.slice(0, 20);
}

async function runTrendHunter() {
  console.log('[TrendHunter] Scraping trends...');
  const [t24, gt] = await Promise.allSettled([scrapeTrends24(), scrapeGoogleTrends()]);
  const all = [];
  if (t24.status === 'fulfilled') all.push(...t24.value);
  if (gt.status === 'fulfilled') all.push(...gt.value);

  // Save to DB via API
  for (const t of all) {
    try {
      await fetch('http://localhost:5000/api/trends', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(t)
      });
    } catch(e) { /* skip duplicates */ }
  }
  console.log(`[TrendHunter] Saved ${all.length} trends`);
}

// Copywriter — generate LinkedIn copy via AI
async function generateCopy(topic, profile, brandVoice) {
  const prompt = `Kamu adalah ${profile.personal_info?.display_name || 'personal branding expert'}.
Tone: ${brandVoice.tone?.primary || 'professional-santai'}
Gaya: Bahasa Indonesia natural, storytelling, personal
Topik: ${topic}

Buat 2 versi post LinkedIn (max 500-1500 karakter):
1. Thought leadership — opini/perspektif pribadi
2. Tips/tutorial — actionable advice

Akhiri dengan CTA ringan (pertanyaan diskusi).
Tambahkan 3-5 hashtag relevan.

Output JSON: {"draft1": "...", "draft2": "..."}`;

  // Placeholder — actual AI call via OpenAI
  return {
    draft1: `[AI-generated draft about: ${topic}]\n\nReplace with actual OpenAI call.`,
    draft2: `[AI-generated draft about: ${topic} - version 2]\n\nReplace with actual OpenAI call.`
  };
}

// Humanizer — refine tone to be more natural
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
  ];
  let result = text;
  for (const [old, neu] of patterns) {
    result = result.replace(new RegExp(old, 'gi'), neu);
  }
  return result;
}

// LinkedIn Poster — post via official API
async function postToLinkedIn(accessToken, body, hashtags) {
  const resp = await fetch('https://api.linkedin.com/rest/posts', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
      'LinkedIn-Version': '202501'
    },
    body: JSON.stringify({
      author: 'urn:li:person:{user_id}',
      lifecycleState: 'PUBLISHED',
      visibility: 'PUBLIC',
      commentary: body + '\n\n' + hashtags
    })
  });
  return resp.ok;
}

module.exports = { scrapeTrends24, scrapeGoogleTrends, runTrendHunter, generateCopy, humanize, postToLinkedIn };
