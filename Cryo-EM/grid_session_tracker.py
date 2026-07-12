#!/usr/bin/env python3
"""
Cryo-EM Grid & Session Tracker
================================
A lightweight Flask + SQLite LIMS-style tool for logging microscope sessions
and the grids screened/collected during each session. Built as a portfolio
demo reflecting the kind of facility-management tooling (resource booking,
grid/puck tracking, PostgreSQL-backed LIMS) used in a real multi-user
cryo-EM facility, scaled down to a single-file, dependency-light app.

Run:
    pip install flask
    python grid_session_tracker.py

Then open http://127.0.0.1:5000 in a browser.

Data is stored in a local SQLite file (grid_tracker.db, created automatically
on first run). Delete that file to reset all data.
"""

import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Flask, g, redirect, render_template_string, request, url_for, jsonify

DB_PATH = Path(__file__).parent / "grid_tracker.db"

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_date TEXT NOT NULL,
            instrument TEXT NOT NULL,
            operator TEXT,
            sample_name TEXT,
            purpose TEXT,
            notes TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS grids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            grid_label TEXT,
            grid_type TEXT,
            ice_quality TEXT,
            outcome TEXT,
            resolution_achieved REAL,
            notes TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
        );
        """
    )
    db.commit()
    db.close()


INSTRUMENTS = ["Titan Krios", "Glacios", "Aquilos 2 FIB-SEM", "Talos Arctica", "Other"]
GRID_TYPES = ["Quantifoil 1.2/1.3", "Quantifoil 2/1", "UltrAuFoil", "C-flat", "Protochips (patterned)", "Other"]
ICE_QUALITY = ["Excellent", "Good", "Fair", "Poor", "Not screened"]
OUTCOMES = ["Collected - high resolution", "Collected - moderate", "Screened only",
           "Discarded - poor ice", "Discarded - broken/contaminated", "Optimization needed"]

# ---------------------------------------------------------------------------
# Templates (kept inline for a single-file, easy-to-review demo)
# ---------------------------------------------------------------------------

BASE_STYLE = """
<style>
  :root { --navy: #1F3864; --blue: #4472A8; --light: #8CA6C9; --bg: #F7F9FC; }
  * { box-sizing: border-box; }
  body { font-family: -apple-system, Segoe UI, Roboto, sans-serif; background: var(--bg);
         color: #222; margin: 0; padding: 0 0 3rem; }
  header { background: var(--navy); color: white; padding: 1.2rem 2rem; }
  header h1 { margin: 0; font-size: 1.4rem; }
  header a { color: white; text-decoration: none; opacity: 0.85; }
  nav { margin-top: 0.4rem; font-size: 0.9rem; }
  nav a { margin-right: 1.2rem; }
  main { max-width: 960px; margin: 2rem auto; padding: 0 1.5rem; }
  .card { background: white; border-radius: 8px; padding: 1.5rem; margin-bottom: 1.2rem;
          box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
  .stats { display: flex; gap: 1rem; flex-wrap: wrap; }
  .stat { flex: 1; min-width: 140px; background: white; border-radius: 8px; padding: 1rem 1.2rem;
          box-shadow: 0 1px 3px rgba(0,0,0,0.08); text-align: center; }
  .stat .num { font-size: 1.8rem; font-weight: 700; color: var(--navy); }
  .stat .label { font-size: 0.8rem; color: #667; text-transform: uppercase; letter-spacing: 0.03em; }
  table { width: 100%; border-collapse: collapse; margin-top: 0.5rem; }
  th, td { text-align: left; padding: 0.5rem 0.6rem; border-bottom: 1px solid #eee; font-size: 0.9rem; }
  th { color: #556; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.03em; }
  a.button, button { background: var(--blue); color: white; border: none; padding: 0.55rem 1.1rem;
          border-radius: 6px; cursor: pointer; text-decoration: none; font-size: 0.88rem; display: inline-block; }
  a.button.secondary { background: #ddd; color: #333; }
  form .field { margin-bottom: 0.9rem; }
  label { display: block; font-size: 0.82rem; color: #445; margin-bottom: 0.25rem; font-weight: 600; }
  input, select, textarea { width: 100%; padding: 0.5rem; border: 1px solid #ccd; border-radius: 5px;
          font-size: 0.92rem; font-family: inherit; }
  textarea { min-height: 60px; }
  .badge { display: inline-block; padding: 0.15rem 0.55rem; border-radius: 10px; font-size: 0.75rem;
          background: var(--light); color: white; }
  .row { display: flex; gap: 1rem; }
  .row > div { flex: 1; }
  .muted { color: #778; font-size: 0.85rem; }
</style>
"""

HEADER = """
<header>
  <h1><a href="{{ url_for('dashboard') }}">Cryo-EM Grid & Session Tracker</a></h1>
  <nav>
    <a href="{{ url_for('dashboard') }}">Dashboard</a>
    <a href="{{ url_for('new_session') }}">+ New Session</a>
    <a href="{{ url_for('api_stats') }}">API: /api/stats</a>
  </nav>
</header>
"""

DASHBOARD_TEMPLATE = BASE_STYLE + HEADER + """
<main>
  <div class="stats">
    <div class="stat"><div class="num">{{ stats.total_sessions }}</div><div class="label">Sessions</div></div>
    <div class="stat"><div class="num">{{ stats.total_grids }}</div><div class="label">Grids logged</div></div>
    <div class="stat"><div class="num">{{ stats.avg_grids }}</div><div class="label">Avg grids / session</div></div>
    <div class="stat"><div class="num">{{ stats.success_rate }}%</div><div class="label">Grids collected</div></div>
  </div>

  <div class="card">
    <h2>Recent Sessions</h2>
    {% if sessions %}
    <table>
      <tr><th>Date</th><th>Instrument</th><th>Sample</th><th>Operator</th><th>Grids</th><th></th></tr>
      {% for s in sessions %}
      <tr>
        <td>{{ s.session_date }}</td>
        <td>{{ s.instrument }}</td>
        <td>{{ s.sample_name or '-' }}</td>
        <td>{{ s.operator or '-' }}</td>
        <td>{{ s.grid_count }}</td>
        <td><a href="{{ url_for('session_detail', session_id=s.id) }}">View →</a></td>
      </tr>
      {% endfor %}
    </table>
    {% else %}
    <p class="muted">No sessions logged yet. <a href="{{ url_for('new_session') }}">Log your first session</a>.</p>
    {% endif %}
  </div>
</main>
"""

SESSION_FORM_TEMPLATE = BASE_STYLE + HEADER + """
<main>
  <div class="card">
    <h2>New Session</h2>
    <form method="post">
      <div class="row">
        <div class="field">
          <label>Date</label>
          <input type="date" name="session_date" value="{{ today }}" required>
        </div>
        <div class="field">
          <label>Instrument</label>
          <select name="instrument">
            {% for inst in instruments %}<option value="{{ inst }}">{{ inst }}</option>{% endfor %}
          </select>
        </div>
      </div>
      <div class="row">
        <div class="field"><label>Operator</label><input type="text" name="operator" placeholder="e.g. Jason Porta"></div>
        <div class="field"><label>Sample Name</label><input type="text" name="sample_name" placeholder="e.g. Apoferritin"></div>
      </div>
      <div class="field"><label>Purpose</label><input type="text" name="purpose" placeholder="e.g. Screening, data collection, benchmark"></div>
      <div class="field"><label>Notes</label><textarea name="notes"></textarea></div>
      <button type="submit">Save Session</button>
      <a class="button secondary" href="{{ url_for('dashboard') }}">Cancel</a>
    </form>
  </div>
</main>
"""

SESSION_DETAIL_TEMPLATE = BASE_STYLE + HEADER + """
<main>
  <div class="card">
    <h2>Session: {{ session.session_date }} — {{ session.instrument }}</h2>
    <p class="muted">Sample: {{ session.sample_name or '-' }} | Operator: {{ session.operator or '-' }} | Purpose: {{ session.purpose or '-' }}</p>
    {% if session.notes %}<p>{{ session.notes }}</p>{% endif %}
  </div>

  <div class="card">
    <h3>Grids in this session</h3>
    {% if grids %}
    <table>
      <tr><th>Label</th><th>Type</th><th>Ice Quality</th><th>Outcome</th><th>Resolution</th></tr>
      {% for grid in grids %}
      <tr>
        <td>{{ grid.grid_label or '-' }}</td>
        <td>{{ grid.grid_type }}</td>
        <td><span class="badge">{{ grid.ice_quality }}</span></td>
        <td>{{ grid.outcome }}</td>
        <td>{{ grid.resolution_achieved and (grid.resolution_achieved ~ ' \u00c5') or '-' }}</td>
      </tr>
      {% endfor %}
    </table>
    {% else %}
    <p class="muted">No grids logged for this session yet.</p>
    {% endif %}
  </div>

  <div class="card">
    <h3>Add a Grid</h3>
    <form method="post" action="{{ url_for('add_grid', session_id=session.id) }}">
      <div class="row">
        <div class="field"><label>Grid Label</label><input type="text" name="grid_label" placeholder="e.g. Grid 3, square A2"></div>
        <div class="field">
          <label>Grid Type</label>
          <select name="grid_type">{% for gt in grid_types %}<option value="{{ gt }}">{{ gt }}</option>{% endfor %}</select>
        </div>
      </div>
      <div class="row">
        <div class="field">
          <label>Ice Quality</label>
          <select name="ice_quality">{% for iq in ice_quality %}<option value="{{ iq }}">{{ iq }}</option>{% endfor %}</select>
        </div>
        <div class="field">
          <label>Outcome</label>
          <select name="outcome">{% for o in outcomes %}<option value="{{ o }}">{{ o }}</option>{% endfor %}</select>
        </div>
      </div>
      <div class="field"><label>Resolution Achieved (\u00c5, optional)</label><input type="number" step="0.01" name="resolution_achieved"></div>
      <div class="field"><label>Notes</label><textarea name="notes"></textarea></div>
      <button type="submit">Add Grid</button>
    </form>
  </div>

  <a class="button secondary" href="{{ url_for('dashboard') }}">← Back to Dashboard</a>
</main>
"""

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def dashboard():
    db = get_db()
    sessions = db.execute(
        """
        SELECT s.*, COUNT(g.id) AS grid_count
        FROM sessions s LEFT JOIN grids g ON g.session_id = s.id
        GROUP BY s.id ORDER BY s.session_date DESC, s.id DESC LIMIT 25
        """
    ).fetchall()

    total_sessions = db.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    total_grids = db.execute("SELECT COUNT(*) FROM grids").fetchone()[0]
    avg_grids = round(total_grids / total_sessions, 1) if total_sessions else 0
    collected = db.execute(
        "SELECT COUNT(*) FROM grids WHERE outcome LIKE 'Collected%'"
    ).fetchone()[0]
    success_rate = round(100 * collected / total_grids) if total_grids else 0

    stats = {
        "total_sessions": total_sessions,
        "total_grids": total_grids,
        "avg_grids": avg_grids,
        "success_rate": success_rate,
    }
    return render_template_string(DASHBOARD_TEMPLATE, sessions=sessions, stats=stats)


@app.route("/sessions/new", methods=["GET", "POST"])
def new_session():
    if request.method == "POST":
        db = get_db()
        db.execute(
            """
            INSERT INTO sessions (session_date, instrument, operator, sample_name, purpose, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                request.form["session_date"],
                request.form["instrument"],
                request.form.get("operator", ""),
                request.form.get("sample_name", ""),
                request.form.get("purpose", ""),
                request.form.get("notes", ""),
                datetime.utcnow().isoformat(),
            ),
        )
        db.commit()
        return redirect(url_for("dashboard"))

    today = datetime.utcnow().strftime("%Y-%m-%d")
    return render_template_string(SESSION_FORM_TEMPLATE, today=today, instruments=INSTRUMENTS)


@app.route("/sessions/<int:session_id>")
def session_detail(session_id):
    db = get_db()
    session = db.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    grids = db.execute(
        "SELECT * FROM grids WHERE session_id = ? ORDER BY id", (session_id,)
    ).fetchall()
    return render_template_string(
        SESSION_DETAIL_TEMPLATE, session=session, grids=grids,
        grid_types=GRID_TYPES, ice_quality=ICE_QUALITY, outcomes=OUTCOMES,
    )


@app.route("/sessions/<int:session_id>/grids/new", methods=["POST"])
def add_grid(session_id):
    db = get_db()
    resolution = request.form.get("resolution_achieved") or None
    db.execute(
        """
        INSERT INTO grids (session_id, grid_label, grid_type, ice_quality, outcome,
                           resolution_achieved, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session_id,
            request.form.get("grid_label", ""),
            request.form.get("grid_type", ""),
            request.form.get("ice_quality", ""),
            request.form.get("outcome", ""),
            float(resolution) if resolution else None,
            request.form.get("notes", ""),
            datetime.utcnow().isoformat(),
        ),
    )
    db.commit()
    return redirect(url_for("session_detail", session_id=session_id))


@app.route("/api/stats")
def api_stats():
    db = get_db()
    total_sessions = db.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    total_grids = db.execute("SELECT COUNT(*) FROM grids").fetchone()[0]
    by_outcome = db.execute(
        "SELECT outcome, COUNT(*) as n FROM grids GROUP BY outcome"
    ).fetchall()
    return jsonify({
        "total_sessions": total_sessions,
        "total_grids": total_grids,
        "grids_by_outcome": {row["outcome"]: row["n"] for row in by_outcome},
    })


@app.route("/api/sessions")
def api_sessions():
    db = get_db()
    sessions = db.execute("SELECT * FROM sessions ORDER BY session_date DESC").fetchall()
    return jsonify([dict(s) for s in sessions])


if __name__ == "__main__":
    init_db()
    print(f"Database: {DB_PATH}")
    print("Starting server at http://127.0.0.1:5000 ...")
    app.run(debug=True)
