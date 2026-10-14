#!/usr/bin/env python3
"""DS LAB backend — Flask + SQLite (single file, stdlib sqlite3, no ORM).

Run:
    pip install flask
    python app.py              ->  http://localhost:5000

Serves the site (index.html, css/, js/) AND persists every bit of data
(profile, experiments, sub-experiments, modules, outputs, videos,
home/about/tools) in dslab.db (SQLite, same folder).

API:
    GET  /api/state            full state JSON
    PUT  /api/state            replace full state (validated, one transaction)

Added in the dashboard update (no table/schema changes): the website logo,
Resources, Projects and the extra Module fields are stored as JSON rows in
the existing `settings` table, so every older record stays untouched.
"""
import json
import os
import sqlite3
from flask import Flask, jsonify, request, send_from_directory

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "dslab.db")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 48 * 1024 * 1024  # photos/files stored as data URLs

SCHEMA = """
CREATE TABLE IF NOT EXISTS profile (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  name TEXT DEFAULT '', roll TEXT DEFAULT '', cls TEXT DEFAULT '',
  uni TEXT DEFAULT '', photo TEXT DEFAULT '', faculty TEXT DEFAULT '',
  designation TEXT DEFAULT '', linkedin TEXT DEFAULT '', github TEXT DEFAULT '',
  youtube TEXT DEFAULT '', email TEXT DEFAULT '', site TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS settings (k TEXT PRIMARY KEY, v TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS experiments (
  id TEXT PRIMARY KEY, ord INTEGER DEFAULT 0,
  title TEXT DEFAULT '', tagline TEXT DEFAULT '', image TEXT DEFAULT '',
  github TEXT DEFAULT '', videoUrl TEXT DEFAULT '', youtube TEXT DEFAULT '[]',
  needsFile INTEGER DEFAULT 0, sampleName TEXT DEFAULT 'data.csv',
  sampleText TEXT DEFAULT '', code TEXT DEFAULT '', expectedOutput TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS subs (
  id TEXT PRIMARY KEY, exp_id TEXT NOT NULL, ord INTEGER DEFAULT 0,
  title TEXT DEFAULT '', descr TEXT DEFAULT '', github TEXT DEFAULT '',
  needsFile INTEGER DEFAULT 0, sampleName TEXT DEFAULT 'data.csv',
  sampleText TEXT DEFAULT '', code TEXT DEFAULT '', expectedOutput TEXT DEFAULT '',
  youtube TEXT DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS modules (
  id TEXT PRIMARY KEY, ord INTEGER DEFAULT 0,
  name TEXT DEFAULT '', descr TEXT DEFAULT '',
  youtube TEXT DEFAULT '', files TEXT DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS outputs (k TEXT PRIMARY KEY, v TEXT DEFAULT '{}');
CREATE TABLE IF NOT EXISTS videos (k TEXT PRIMARY KEY, v TEXT DEFAULT '');
CREATE INDEX IF NOT EXISTS idx_subs_exp ON subs (exp_id);
"""

PROFILE_COLS = ["name", "roll", "cls", "uni", "photo", "faculty",
                "designation", "linkedin", "github", "youtube", "email", "site"]

SEED_PROFILE = {  # blank on purpose: enter your details in the profile editor
    "name": "", "roll": "", "cls": "",
    "uni": "", "photo": "", "faculty": "",
    "designation": "", "linkedin": "", "github": "", "youtube": "",
    "email": "", "site": "",
}
SEED_HOME = {
    "title": "Data Science",
    "subtitle": "Your Digital Library for Learning, Experiments and Projects",
}
SEED_ABOUT = (
    "This site is my complete digital record for the Data Science Laboratory course. "
    "Each experiment carries an intro video, GitHub-linked Python code that runs in the browser, "
    "CSV upload for real data extraction, expected outputs, and output-file uploads for lab-record "
    "evidence. Sub-experiments break every experiment into evaluable units. The Modules tab holds "
    "study material, and everything is tied to one student profile."
)
SEED_TOOLS = [
    {"id": "t1", "icon": "🐍", "name": "Python", "desc": "Core language"},
    {"id": "t2", "icon": "🐼", "name": "Pandas", "desc": "DataFrames & EDA"},
    {"id": "t3", "icon": "🔢", "name": "NumPy", "desc": "Arrays & maths"},
    {"id": "t4", "icon": "📊", "name": "Matplotlib", "desc": "Charts & plots"},
    {"id": "t5", "icon": "🌊", "name": "Seaborn", "desc": "Statistical viz"},
    {"id": "t6", "icon": "🌲", "name": "Scikit-learn", "desc": "ML models"},
    {"id": "t7", "icon": "📓", "name": "Jupyter", "desc": "Lab notebooks"},
    {"id": "t8", "icon": "🐙", "name": "GitHub", "desc": "Code record"},
]


def connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    """Create tables + seed first-run defaults (idempotent, never overwrites)."""
    con = connect()
    try:
        con.executescript(SCHEMA)
        has = con.execute("SELECT COUNT(*) AS c FROM profile WHERE id=1").fetchone()["c"]
        if not has:
            con.execute(
                "INSERT INTO profile (id,name,roll,cls,uni,photo,faculty,designation,"
                "linkedin,github,youtube,email,site) VALUES (1,?,?,?,?,?,?,?,?,?,?,?,?)",
                tuple(SEED_PROFILE[c] for c in PROFILE_COLS),
            )
        for k, v in (("home", json.dumps(SEED_HOME)),
                     ("about", SEED_ABOUT),
                     ("tools", json.dumps(SEED_TOOLS)),
                     ("logo", ""),
                     ("resources", "[]"),
                     ("projects", "[]"),
                     ("module_extra", "{}")):
            con.execute("INSERT OR IGNORE INTO settings (k,v) VALUES (?,?)", (k, v))
        con.commit()
    finally:
        con.close()


def jload(s, fb):
    try:
        return json.loads(s) if s else fb
    except Exception:
        return fb


def s(x):
    return x if isinstance(x, str) else ("" if x is None else str(x))


def b(x):
    return 1 if x else 0


@app.route("/api/state", methods=["GET"])
def api_get():
    con = connect()
    try:
        p = con.execute("SELECT * FROM profile WHERE id=1").fetchone()
        profile = {c: (p[c] if p[c] is not None else "") for c in PROFILE_COLS} if p else dict(SEED_PROFILE)
        sets = {r["k"]: r["v"] for r in con.execute("SELECT k,v FROM settings")}
        home = jload(sets.get("home"), None) or dict(SEED_HOME)
        about = sets.get("about") or SEED_ABOUT
        tools = jload(sets.get("tools"), None)
        if not isinstance(tools, list):
            tools = []
        exps = []
        for r in con.execute("SELECT * FROM experiments ORDER BY ord, rowid"):
            exps.append({
                "id": r["id"], "title": r["title"] or "", "tagline": r["tagline"] or "",
                "image": r["image"] or "", "github": r["github"] or "",
                "videoUrl": r["videoUrl"] or "", "youtube": jload(r["youtube"], []),
                "needsFile": bool(r["needsFile"]), "sampleName": r["sampleName"] or "data.csv",
                "sampleText": r["sampleText"] or "", "code": r["code"] or "",
                "expectedOutput": r["expectedOutput"] or "",
                "subs": [{
                    "id": x["id"], "title": x["title"] or "", "desc": x["descr"] or "",
                    "github": x["github"] or "", "needsFile": bool(x["needsFile"]),
                    "sampleName": x["sampleName"] or "data.csv",
                    "sampleText": x["sampleText"] or "", "code": x["code"] or "",
                    "expectedOutput": x["expectedOutput"] or "",
                    "youtube": jload(x["youtube"], []),
                } for x in con.execute("SELECT * FROM subs WHERE exp_id=? ORDER BY ord, rowid", (r["id"],))],
            })
        mx = jload(sets.get("module_extra"), {})
        if not isinstance(mx, dict):
            mx = {}
        mods = [{
            "id": r["id"], "name": r["name"] or "", "desc": r["descr"] or "",
            "youtube": r["youtube"] or "", "files": jload(r["files"], []),
            "info": s((mx.get(r["id"]) or {}).get("info")),
            "links": (mx.get(r["id"]) or {}).get("links") or [],
        } for r in con.execute("SELECT * FROM modules ORDER BY ord, rowid")]
        resources = jload(sets.get("resources"), [])
        projects = jload(sets.get("projects"), [])
        outputs = {r["k"]: jload(r["v"], {}) for r in con.execute("SELECT k,v FROM outputs")}
        videos = {r["k"]: (r["v"] or "") for r in con.execute("SELECT k,v FROM videos")}
        return jsonify({"version": 2, "profile": profile, "home": home,
                        "about": about, "tools": tools, "experiments": exps,
                        "modules": mods, "outputs": outputs, "videos": videos,
                        "logo": sets.get("logo") or "",
                        "resources": resources if isinstance(resources, list) else [],
                        "projects": projects if isinstance(projects, list) else []})
    finally:
        con.close()


@app.route("/api/state", methods=["PUT"])
def api_put():
    try:
        st = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON body"}), 400
    if not isinstance(st, dict) or st.get("version") != 2 or not isinstance(st.get("experiments"), list):
        return jsonify({"error": "Invalid state payload"}), 400
    con = connect()
    try:
        con.execute("BEGIN")
        p = st.get("profile", {}) or {}
        con.execute(
            "UPDATE profile SET name=?,roll=?,cls=?,uni=?,photo=?,faculty=?,"
            "designation=?,linkedin=?,github=?,youtube=?,email=?,site=? WHERE id=1",
            tuple(s(p.get(c, "")) for c in PROFILE_COLS),
        )
        con.execute("UPDATE settings SET v=? WHERE k='home'", (json.dumps(st.get("home") or {}),))
        if "about" in st:  # About section was removed from the UI; keep any old row untouched
            con.execute("UPDATE settings SET v=? WHERE k='about'", (s(st.get("about", "")),))
        con.execute("UPDATE settings SET v=? WHERE k='tools'", (json.dumps(st.get("tools") or []),))
        con.execute("DELETE FROM subs")
        con.execute("DELETE FROM experiments")
        for i, e in enumerate(st.get("experiments") or []):
            if not isinstance(e, dict) or not e.get("id"):
                continue
            con.execute(
                "INSERT INTO experiments (id,ord,title,tagline,image,github,videoUrl,"
                "youtube,needsFile,sampleName,sampleText,code,expectedOutput)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (s(e.get("id")), i, s(e.get("title")), s(e.get("tagline")), s(e.get("image")),
                 s(e.get("github")), s(e.get("videoUrl")), json.dumps(e.get("youtube") or []),
                 b(e.get("needsFile")), s(e.get("sampleName") or "data.csv"),
                 s(e.get("sampleText")), s(e.get("code")), s(e.get("expectedOutput"))),
            )
            for j, sb in enumerate(e.get("subs") or []):
                if not isinstance(sb, dict) or not sb.get("id"):
                    continue
                con.execute(
                    "INSERT INTO subs (id,exp_id,ord,title,descr,github,needsFile,"
                    "sampleName,sampleText,code,expectedOutput,youtube)"
                    " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (s(sb.get("id")), s(e.get("id")), j, s(sb.get("title")), s(sb.get("desc")),
                     s(sb.get("github")), b(sb.get("needsFile")),
                     s(sb.get("sampleName") or "data.csv"), s(sb.get("sampleText")),
                     s(sb.get("code")), s(sb.get("expectedOutput")),
                     json.dumps(sb.get("youtube") or [])),
                )
        con.execute("DELETE FROM modules")
        for i, m in enumerate(st.get("modules") or []):
            if not isinstance(m, dict) or not m.get("id"):
                continue
            con.execute(
                "INSERT INTO modules (id,ord,name,descr,youtube,files) VALUES (?,?,?,?,?,?)",
                (s(m.get("id")), i, s(m.get("name")), s(m.get("desc")),
                 s(m.get("youtube")), json.dumps(m.get("files") or [])),
            )
        # --- dashboard additions (stored in `settings`, same transaction) ---
        extras = {}
        for m in (st.get("modules") or []):
            if isinstance(m, dict) and m.get("id"):
                extras[s(m.get("id"))] = {
                    "info": s(m.get("info")),
                    "links": m.get("links") if isinstance(m.get("links"), list) else [],
                }
        con.execute("INSERT OR REPLACE INTO settings (k,v) VALUES ('module_extra',?)", (json.dumps(extras),))
        if "logo" in st:
            con.execute("INSERT OR REPLACE INTO settings (k,v) VALUES ('logo',?)", (s(st.get("logo")),))
        for key in ("resources", "projects"):
            if isinstance(st.get(key), list):
                clean = [x for x in st[key] if isinstance(x, dict) and x.get("id")]
                con.execute("INSERT OR REPLACE INTO settings (k,v) VALUES (?,?)", (key, json.dumps(clean)))
        con.execute("DELETE FROM outputs")
        for k, v in (st.get("outputs") or {}).items():
            con.execute("INSERT INTO outputs (k,v) VALUES (?,?)", (s(k), json.dumps(v)))
        con.execute("DELETE FROM videos")
        for k, v in (st.get("videos") or {}).items():
            con.execute("INSERT INTO videos (k,v) VALUES (?,?)", (s(k), s(v)))
        con.commit()
        return jsonify({"ok": True})
    except Exception as ex:  # pragma: no cover - defensive
        con.rollback()
        return jsonify({"error": str(ex)[:300]}), 500
    finally:
        con.close()


@app.route("/")
def index():
    return send_from_directory(BASE, "index.html")



@app.route("/<path:path>")
def static_files(path):
    if path.startswith("api/"):
        return jsonify({"error": "not found"}), 404

    # Never return index.html when a JavaScript or CSS file is missing.
    if path.startswith(("css/", "js/", "assets/")):
        file_path = os.path.join(BASE, path)
        if os.path.isfile(file_path):
            return send_from_directory(BASE, path)
        return jsonify({"error": f"File not found: {path}"}), 404

    return send_from_directory(BASE, "index.html")


init_db()

if __name__ == "__main__":
    print("DS LAB running at http://localhost:5000   (data saved in dslab.db)")
    app.run(host="0.0.0.0", port=5000, debug=False)
