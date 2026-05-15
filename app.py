
import os, json, sqlite3, hashlib, hmac, time, logging
from datetime import datetime, timezone, timedelta
from functools import wraps
from pathlib import Path

from flask import (
    Flask, request, jsonify, send_from_directory,
    redirect, session as flask_session
)
from dotenv import load_dotenv

load_dotenv()

BASE = Path(__file__).parent.resolve()
DB_PATH = BASE / "data" / "app.db"
LOG_PATH = BASE / "logs" / "app.log"

os.makedirs(BASE / "data", exist_ok=True)
os.makedirs(BASE / "logs", exist_ok=True)

logging.basicConfig(
    filename=LOG_PATH, level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

app = Flask(__name__, static_folder=str(BASE / "web" / "public"))
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-me")

# ── Database ────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS trends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            source TEXT NOT NULL,
            score INTEGER DEFAULT 0,
            relevance TEXT DEFAULT '',
            angle TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now'))
        );
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
    """)
    conn.commit()
    conn.close()
    log.info("Database initialized")

init_db()

# ── Helpers ─────────────────────────────────────────────────────────
def json_res(data, status=200):
    return jsonify(data), status

def api_guard(f):
    @wraps(f)
    def wrapper(*a, **kw):
        try:
            return f(*a, **kw)
        except Exception as e:
            log.error(f"API error: {e}")
            return json_res({"error": str(e)}, 500)
    return wrapper

# ── Routes ──────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

# ---- Status ----
@app.get("/api/status")
@api_guard
def api_status():
    conn = get_db()
    draft_count = conn.execute("SELECT COUNT(*) FROM drafts").fetchone()[0]
    post_count = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    trend_count = conn.execute("SELECT COUNT(*) FROM trends").fetchone()[0]
    conn.close()
    return json_res({
        "status": "ok",
        "version": "1.0.0",
        "stats": {
            "drafts": draft_count,
            "posts": post_count,
            "trends": trend_count
        },
        "db_path": str(DB_PATH)
    })

# ---- Trends ----
@app.get("/api/trends")
@api_guard
def api_trends():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM trends ORDER BY score DESC, created_at DESC LIMIT 50"
    ).fetchall()
    conn.close()
    return json_res({"trends": [dict(r) for r in rows]})

@app.post("/api/trends")
@api_guard
def api_add_trend():
    data = request.get_json(force=True)
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO trends (topic, source, score, relevance, angle) VALUES (?,?,?,?,?)",
        (data["topic"], data.get("source","manual"),
         data.get("score",0), data.get("relevance",""), data.get("angle",""))
    )
    conn.commit()
    conn.close()
    return json_res({"id": cur.lastrowid}, 201)

# ---- Drafts ----
@app.get("/api/drafts")
@api_guard
def api_drafts():
    conn = get_db()
    status = request.args.get("status", "")
    if status:
        rows = conn.execute(
            "SELECT d.*, t.topic FROM drafts d LEFT JOIN trends t ON d.topic_id=t.id WHERE d.status=? ORDER BY d.created_at DESC",
            (status,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT d.*, t.topic FROM drafts d LEFT JOIN trends t ON d.topic_id=t.id ORDER BY d.created_at DESC"
        ).fetchall()
    conn.close()
    return json_res({"drafts": [dict(r) for r in rows]})

@app.post("/api/draft/generate")
@api_guard
def api_generate_draft():
    """Placeholder — real AI generation will be in agents/copywriter.py"""
    data = request.get_json(force=True)
    body = data.get("body", "Draft generated by AI (placeholder)")
    hashtags = data.get("hashtags", "#PersonalBranding")
    topic_id = data.get("topic_id")
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO drafts (topic_id, body, hashtags, status) VALUES (?,?,?,?)",
        (topic_id, body, hashtags, "draft")
    )
    conn.commit()
    conn.close()
    return json_res({"id": cur.lastrowid, "status": "draft"}, 201)

@app.post("/api/draft/<int:draft_id>/approve")
@api_guard
def api_approve_draft(draft_id):
    conn = get_db()
    conn.execute("UPDATE drafts SET status='approved' WHERE id=?", (draft_id,))
    conn.commit()
    conn.close()
    return json_res({"status": "approved"})

@app.post("/api/draft/<int:draft_id>/reject")
@api_guard
def api_reject_draft(draft_id):
    conn = get_db()
    conn.execute("UPDATE drafts SET status='rejected' WHERE id=?", (draft_id,))
    conn.commit()
    conn.close()
    return json_res({"status": "rejected"})

@app.post("/api/draft/<int:draft_id>/schedule")
@api_guard
def api_schedule_draft(draft_id):
    data = request.get_json(force=True)
    scheduled = data.get("scheduled_at", datetime.now(timezone.utc).isoformat())
    conn = get_db()
    conn.execute(
        "UPDATE drafts SET status='scheduled', scheduled_at=? WHERE id=?",
        (scheduled, draft_id)
    )
    conn.commit()
    conn.close()
    return json_res({"status": "scheduled", "scheduled_at": scheduled})

# ---- Posts / History ----
@app.get("/api/history")
@api_guard
def api_history():
    conn = get_db()
    rows = conn.execute(
        """SELECT p.*, d.body as draft_body, d.hashtags
           FROM posts p JOIN drafts d ON p.draft_id=d.id
           ORDER BY p.posted_at DESC LIMIT 50"""
    ).fetchall()
    conn.close()
    return json_res({"posts": [dict(r) for r in rows]})

@app.post("/api/post/now")
@api_guard
def api_post_now():
    """Placeholder — real posting via agents/linkedin_client.py"""
    data = request.get_json(force=True)
    draft_id = data.get("draft_id")
    conn = get_db()
    draft = conn.execute("SELECT * FROM drafts WHERE id=?", (draft_id,)).fetchone()
    if not draft:
        return json_res({"error": "Draft not found"}, 404)
    cur = conn.execute(
        "INSERT INTO posts (draft_id, platform) VALUES (?,?)",
        (draft_id, "linkedin")
    )
    conn.execute("UPDATE drafts SET status='posted', posted_at=datetime('now') WHERE id=?", (draft_id,))
    conn.commit()
    conn.close()
    return json_res({"id": cur.lastrowid, "status": "posted"})

# ---- Settings ----
@app.get("/api/settings")
@api_guard
def api_get_settings():
    conn = get_db()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    return json_res({r["key"]: r["value"] for r in rows})

@app.put("/api/settings")
@api_guard
def api_update_settings():
    data = request.get_json(force=True)
    conn = get_db()
    for key, value in data.items():
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=?",
            (key, value, value)
        )
    conn.commit()
    conn.close()
    return json_res({"status": "saved"})

# ---- Profile ----
@app.get("/api/profile")
@api_guard
def api_get_profile():
    profile_path = BASE / "knowledge_base" / "profile.json"
    if not profile_path.exists():
        return json_res({"profile": {}})
    with open(profile_path) as f:
        profile = json.load(f)
    return json_res({"profile": profile})

@app.get("/api/profile/suggestions")
@api_guard
def api_get_suggestions():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM profile_suggestions ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return json_res({"suggestions": [dict(r) for r in rows]})

@app.post("/api/profile/suggestion/<int:sid>/approve")
@api_guard
def api_approve_suggestion(sid):
    conn = get_db()
    conn.execute("UPDATE profile_suggestions SET status='approved' WHERE id=?", (sid,))
    conn.commit()
    conn.close()
    return json_res({"status": "approved"})

# ---- Scheduler placeholder ----
def scheduled_post():
    log.info("Scheduler tick — checking for drafts to post...")
    conn = get_db()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M")
    rows = conn.execute(
        "SELECT * FROM drafts WHERE status='scheduled' AND scheduled_at <= ?",
        (now,)
    ).fetchall()
    for r in rows:
        log.info(f"Auto-posting draft #{r['id']}")
        conn.execute(
            "INSERT INTO posts (draft_id, platform) VALUES (?,?)",
            (r["id"], "linkedin")
        )
        conn.execute(
            "UPDATE drafts SET status='posted', posted_at=datetime('now') WHERE id=?",
            (r["id"],)
        )
    conn.commit()
    conn.close()

# ── Main ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Start scheduler in-thread for dev
    from apscheduler.schedulers.background import BackgroundScheduler
    sched = BackgroundScheduler()
    sched.add_job(scheduled_post, "interval", minutes=15, id="post_check")
    sched.start()
    log.info("copywrAIter started on http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
