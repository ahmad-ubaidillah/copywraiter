# Autonomous Personal Branding Agent — Knowledge Base

## Cara Pakai
1. Isi file `profile.json` dengan data diri kamu
2. Upload 3-5 post LinkedIn terbaik kamu ke `samples/`
3. Isi `brand_voice.json` — tone, gaya bahasa, dll
4. Selesai. Agent bakal pake ini sebagai acuan nulis & optimize profile.

---

## 1. Profile User

Buka LinkedIn → Profile → Edit → Copy paste data

### `knowledge_base/profile.json`

```json
{
  "personal_info": {
    "full_name": "Ahmad Ubaidillah",
    "display_name": "Ahmad U.",
    "headline": "Software Engineer | AI Automation Enthusiast | n8n & AI Agent Builder",
    "location": "Indonesia",
    "industry": "Information Technology & Services"
  },
  "about": {
    "current": "Tulis about section kamu yang sekarang...",
    "target_audience": "Siapa yang mau kamu reach? (e.g., startup founders, fellow devs, HR)",
    "goal": "Personal branding sebagai apa? (e.g., AI automation expert, n8n specialist)"
  },
  "experience": [
    {
      "title": "Software Engineer",
      "company": "Nama Company",
      "start_date": "2023-01",
      "end_date": "present",
      "description_current": "Deskripsi yang sekarang...",
      "highlights": [
        "Achievement/project yang worth mention",
        "Tech stack yang kamu pake"
      ]
    }
  ],
  "education": [
    {
      "school": "Nama Universitas",
      "degree": "S1 Teknik Informatika",
      "year": "2020-2024"
    }
  ],
  "skills": ["Python", "JavaScript", "n8n", "AI Agent", "Automation", "Node.js", "Linux"],
  "certifications": [],
  "languages": [
    { "language": "Indonesia", "proficiency": "Native" },
    { "language": "English", "proficiency": "Professional" }
  ],
  "urls": {
    "github": "https://github.com/username",
    "website": "",
    "portfolio": ""
  }
}
```

---

## 2. Brand Voice

Ini yang paling penting — ini yang bikin AI nulis **seperti kamu**, bukan kayak robot.

### `knowledge_base/brand_voice.json`

```json
{
  "tone": {
    "primary": "professional-santai",
    "description": "Profesional tapi gak kaku. Kayak ngobrol sama senior yang asik.",
    "vibes": ["analoginya bagus", "personal", "ada cerita", "gak menggurui"]
  },
  "language": {
    "primary": "id",
    "style": "Indonesia informal, campur istilah Inggris dikit",
    "avoid": [
      "klise kayak 'synergy', 'leverage', 'think outside the box'",
      "bahasa terlalu formal kaku",
      "sok tahu / bombastis"
    ]
  },
  "post_style": {
    "hook": "Buka dengan pertanyaan atau pernyataan yang bikin penasaran",
    "storytelling": "Ada struktur: masalah → proses → pelajaran",
    "ending": "Call to action ringan: 'gimana menurut kamu?', 'ada yang pernah ngalamin juga?'",
    "length": "500-1500 karakter (LinkedIn ideal)",
    "formatting": "Paragraf pendek, sparing pake line breaks, bold buat poin penting"
  },
  "content_mix": {
    "thought_leadership": {
      "pct": 35,
      "description": "Pendapat orisinal tentang tren industri"
    },
    "tutorial_tips": {
      "pct": 30,
      "description": "Step-by-step, tips, trik"
    },
    "personal_story": {
      "pct": 20,
      "description": "Cerita dari pengalaman nyata"
    },
    "engagement": {
      "pct": 10,
      "description": "Poll, question, diskusi"
    },
    "repost_opinion": {
      "pct": 5,
      "description": "Share post orang + komentar"
    }
  },
  "hashtag_strategy": {
    "max_per_post": 5,
    "preferred": ["#AI", "#Automation", "#n8n", "#PersonalBranding", "#TechIndonesia", "#SoftwareEngineer"],
    "avoid": ["#follow", "#like", "#viral"]
  },
  "topics_to_avoid": [
    "Politik Indonesia",
    "SARA",
    "Kontroversi perusahaan tertentu",
    "Gosip industri"
  ]
}
```

---

## 3. Sample Posts

Ambil 3-5 post LinkedIn kamu yang **paling banyak engagement-nya**. 
Simpan di folder `knowledge_base/samples/` dengan format:

### `knowledge_base/samples/post_01.md`
```
LINK: https://linkedin.com/posts/...
TANGGAL: 2026-04-20
ENGAGEMENT: 150 likes, 25 comments
---
[Copy paste isi post kamu di sini...]
```

Buat 3-5 file seperti ini. Agent bakal belajar pola tulisan kamu dari sini.

---

## 4. Content Calendar

### `knowledge_base/content_calendar.json`

```json
{
  "schedule": {
    "times_per_day": 2,
    "preferred_hours": ["07:00", "19:00 WIB"],
    "timezone": "Asia/Jakarta"
  },
  "posting_days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
  "weekend_posting": false
}
```

---

## 5. Auto-Reply Settings (Opsional)

### `knowledge_base/auto_reply.json`

```json
{
  "enabled": false,
  "reply_to_comments": false,
  "reply_to_dm": false,
  "notes": "Fitur ini menyusul. Nanti agent bisa bales komentar di postnya sendiri."
}
```

---

## 6. Profile Audit Goals

### `knowledge_base/profile_goals.json`

Ini target buat Agent Profile Optimizer:

```json
{
  "target_headline": "AI Automation Builder & n8n Enthusiast | Bikin workflow pintar yang kerja 24/7",
  "about_goals": {
    "structure": "Hook → Who I help → How I do it → Proof → CTA",
    "max_chars": 2000,
    "include_keywords": ["n8n", "AI Agent", "automation", "workflow", "personal branding"]
  },
  "experience_goals": {
    "use_action_verbs": true,
    "include_metrics": true,
    "max_bullets_per_role": 5
  },
  "frequency": "monthly"
}
```

---

## Cara Mulai

1. Isi `profile.json` dengan data kamu
2. Isi `brand_voice.json` — ini yang paling penting
3. Kumpulin 3 sample post → masukin ke `samples/`
4. Sisanya default dulu, bisa diubah kapan aja

Kalau udah siap, gue bakal setup Agent 1 (Trend Hunter) dan Agent 2 (Copywriter). Agent 3 (Profile Optimizer) nyusul setelah lo approve saran perbaikannya.
