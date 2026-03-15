import os
import sqlite3
from datetime import datetime, timezone
from flask import Flask, jsonify, render_template, request, url_for, session, redirect
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")
app.config["DATABASE"] = os.environ.get(
    "DATABASE_PATH",
    os.path.join(app.root_path, "tide.db"),
)

# OAuth Configuration
client_id = os.environ.get("GOOGLE_CLIENT_ID")
client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")

if not client_id or not client_secret:
    print("WARNING: GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET is missing from environment!")
else:
    print(f"OAuth Config Loaded: ID starts with {client_id[:10]}...")

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=client_id,
    client_secret=client_secret,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# --- SQLite Store ---

def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

SEED_USER = {
    "email": "seed@tide.local",
    "sub": "seed-user",
    "display_name": "TIDE Seed Data",
    "identifier": "seed@tide.local",
}

SEED_SITES = [
    {
        "name": "Molasses Reef",
        "lat": 25.0097,
        "lng": -80.3762,
        "region": "Key Largo",
        "difficulty": "Open Water",
        "depth_ft": 35,
        "visibility_ft": 60,
        "notes": "Shallow coral formations with easy boat access.",
        "added_at": "2026-03-10T14:00:00+00:00",
        "updated_at": "2026-03-10T14:00:00+00:00",
        "added_by": SEED_USER,
        "updated_by": SEED_USER,
    },
    {
        "name": "French Reef",
        "lat": 25.0255,
        "lng": -80.3529,
        "region": "Key Largo",
        "difficulty": "Open Water",
        "depth_ft": 28,
        "visibility_ft": 55,
        "notes": "Popular reef line for survey and beginner drift dives.",
        "added_at": "2026-03-11T14:00:00+00:00",
        "updated_at": "2026-03-11T14:00:00+00:00",
        "added_by": SEED_USER,
        "updated_by": SEED_USER,
    },
    {
        "name": "Sombrero Reef",
        "lat": 24.6266,
        "lng": -81.1102,
        "region": "Marathon",
        "difficulty": "Advanced",
        "depth_ft": 42,
        "visibility_ft": 70,
        "notes": "Strong current windows; best with experienced buddies.",
        "added_at": "2026-03-12T14:00:00+00:00",
        "updated_at": "2026-03-12T14:00:00+00:00",
        "added_by": SEED_USER,
        "updated_by": SEED_USER,
    },
    {
        "name": "Looe Key",
        "lat": 24.5481,
        "lng": -81.4068,
        "region": "Lower Keys",
        "difficulty": "Open Water",
        "depth_ft": 30,
        "visibility_ft": 65,
        "notes": "High biodiversity and wide reef structure for photography.",
        "added_at": "2026-03-13T14:00:00+00:00",
        "updated_at": "2026-03-13T14:00:00+00:00",
        "added_by": SEED_USER,
        "updated_by": SEED_USER,
    },
]


def get_db_connection():
    connection = sqlite3.connect(app.config["DATABASE"])
    connection.row_factory = sqlite3.Row
    return connection


class DiveSiteStore:
    def __init__(self, db_path):
        self.db_path = db_path
        self.initialize()

    def initialize(self):
        with get_db_connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS dive_sites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    lat REAL NOT NULL,
                    lng REAL NOT NULL,
                    region TEXT NOT NULL,
                    difficulty TEXT NOT NULL,
                    depth_ft INTEGER NOT NULL,
                    visibility_ft INTEGER NOT NULL,
                    notes TEXT NOT NULL,
                    added_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    added_by_email TEXT,
                    added_by_sub TEXT,
                    added_by_display_name TEXT,
                    added_by_identifier TEXT,
                    updated_by_email TEXT,
                    updated_by_sub TEXT,
                    updated_by_display_name TEXT,
                    updated_by_identifier TEXT
                )
                """
            )

            existing_rows = connection.execute(
                "SELECT COUNT(*) AS count FROM dive_sites"
            ).fetchone()["count"]
            if existing_rows == 0:
                for site in SEED_SITES:
                    connection.execute(
                        """
                        INSERT INTO dive_sites (
                            name, lat, lng, region, difficulty, depth_ft, visibility_ft, notes,
                            added_at, updated_at,
                            added_by_email, added_by_sub, added_by_display_name, added_by_identifier,
                            updated_by_email, updated_by_sub, updated_by_display_name, updated_by_identifier
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        self._site_values(site),
                    )
            connection.commit()

    def _actor_from_row(self, prefix, row):
        return {
            "email": row[f"{prefix}_email"],
            "sub": row[f"{prefix}_sub"],
            "display_name": row[f"{prefix}_display_name"],
            "identifier": row[f"{prefix}_identifier"],
        }

    def _row_to_site(self, row):
        return {
            "id": row["id"],
            "name": row["name"],
            "lat": row["lat"],
            "lng": row["lng"],
            "region": row["region"],
            "difficulty": row["difficulty"],
            "depth_ft": row["depth_ft"],
            "visibility_ft": row["visibility_ft"],
            "notes": row["notes"],
            "added_at": row["added_at"],
            "updated_at": row["updated_at"],
            "added_by": self._actor_from_row("added_by", row),
            "updated_by": self._actor_from_row("updated_by", row),
        }

    def _site_values(self, site):
        added_by = site["added_by"]
        updated_by = site["updated_by"]
        return (
            site["name"],
            site["lat"],
            site["lng"],
            site["region"],
            site["difficulty"],
            site["depth_ft"],
            site["visibility_ft"],
            site["notes"],
            site["added_at"],
            site["updated_at"],
            added_by.get("email"),
            added_by.get("sub"),
            added_by.get("display_name"),
            added_by.get("identifier"),
            updated_by.get("email"),
            updated_by.get("sub"),
            updated_by.get("display_name"),
            updated_by.get("identifier"),
        )

    def list_sites(self):
        with get_db_connection() as connection:
            rows = connection.execute(
                "SELECT * FROM dive_sites ORDER BY id"
            ).fetchall()
        return [self._row_to_site(row) for row in rows]

    def get_site(self, site_id):
        with get_db_connection() as connection:
            row = connection.execute(
                "SELECT * FROM dive_sites WHERE id = ?",
                (site_id,),
            ).fetchone()
        return self._row_to_site(row) if row else None

    def create_site(self, payload, actor):
        timestamp = now_iso()
        with get_db_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO dive_sites (
                    name, lat, lng, region, difficulty, depth_ft, visibility_ft, notes,
                    added_at, updated_at,
                    added_by_email, added_by_sub, added_by_display_name, added_by_identifier,
                    updated_by_email, updated_by_sub, updated_by_display_name, updated_by_identifier
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["name"],
                    payload["lat"],
                    payload["lng"],
                    payload["region"],
                    payload["difficulty"],
                    payload["depth_ft"],
                    payload["visibility_ft"],
                    payload["notes"],
                    timestamp,
                    timestamp,
                    actor.get("email"),
                    actor.get("sub"),
                    actor.get("display_name"),
                    actor.get("identifier"),
                    actor.get("email"),
                    actor.get("sub"),
                    actor.get("display_name"),
                    actor.get("identifier"),
                ),
            )
            connection.commit()
            site_id = cursor.lastrowid
        return self.get_site(site_id)

    def update_site(self, site_id, payload, actor):
        with get_db_connection() as connection:
            cursor = connection.execute(
                """
                UPDATE dive_sites
                SET name = ?, lat = ?, lng = ?, region = ?, difficulty = ?, depth_ft = ?,
                    visibility_ft = ?, notes = ?, updated_at = ?, updated_by_email = ?,
                    updated_by_sub = ?, updated_by_display_name = ?, updated_by_identifier = ?
                WHERE id = ?
                """,
                (
                    payload["name"],
                    payload["lat"],
                    payload["lng"],
                    payload["region"],
                    payload["difficulty"],
                    payload["depth_ft"],
                    payload["visibility_ft"],
                    payload["notes"],
                    now_iso(),
                    actor.get("email"),
                    actor.get("sub"),
                    actor.get("display_name"),
                    actor.get("identifier"),
                    site_id,
                ),
            )
            connection.commit()
            if cursor.rowcount == 0:
                return None
        return self.get_site(site_id)

store = DiveSiteStore(app.config["DATABASE"])

# --- Auth Helpers (formerly app/auth.py) ---

def get_current_user():
    user = session.get('user')
    if not user:
        return None
    return user

def require_auth():
    user = get_current_user()
    if not user:
        return None, (jsonify({"error": "Authentication required."}), 401)
    return user, None

# --- Routes (formerly app/routes.py) ---

def normalize_site_payload(payload):
    required_fields = ["name", "region", "difficulty", "notes", "lat", "lng", "depth_ft", "visibility_ft"]
    missing = [field for field in required_fields if field not in payload]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

    normalized = {
        "name": str(payload.get("name", "")).strip(),
        "region": str(payload.get("region", "")).strip(),
        "difficulty": str(payload.get("difficulty", "")).strip(),
        "notes": str(payload.get("notes", "")).strip(),
        "lat": float(payload.get("lat", 0)),
        "lng": float(payload.get("lng", 0)),
        "depth_ft": int(payload.get("depth_ft", 0)),
        "visibility_ft": int(payload.get("visibility_ft", 0)),
    }

    if not normalized["name"]: raise ValueError("Name is required.")
    if not normalized["region"]: raise ValueError("Region is required.")
    if not (-90 <= normalized["lat"] <= 90): raise ValueError("Latitude must be between -90 and 90.")
    if not (-180 <= normalized["lng"] <= 180): raise ValueError("Longitude must be between -180 and 180.")
    if normalized["depth_ft"] < 0 or normalized["visibility_ft"] < 0:
        raise ValueError("Depth and visibility must be non-negative.")

    return normalized

@app.route("/")
def index():
    return render_template("index.html", user=get_current_user())

# --- OAuth Routes ---

@app.route("/login")
def login():
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route("/authorize")
def authorize():
    token = google.authorize_access_token()
    user_info = token.get('userinfo')
    if user_info:
        session['user'] = {
            "email": user_info.get("email"),
            "sub": user_info.get("sub"),
            "display_name": user_info.get("name") or user_info.get("email"),
            "identifier": user_info.get("email") or user_info.get("sub"),
        }
    return redirect(url_for('index'))

@app.route("/logout")
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

# --- API Routes ---

@app.route("/api/dive-sites")
def get_dive_sites():
    return jsonify(store.list_sites())

@app.route("/api/dive-sites/<int:site_id>")
def get_dive_site(site_id):
    site = store.get_site(site_id)
    if not site:
        return jsonify({"error": "Dive site not found."}), 404
    return jsonify(site)

@app.route("/api/dive-sites", methods=["POST"])
def create_dive_site():
    actor, error_response = require_auth()
    if error_response:
        return error_response

    payload = request.get_json(silent=True) or {}
    try:
        normalized = normalize_site_payload(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    site = store.create_site(normalized, actor)
    return jsonify(site), 201

@app.route("/api/dive-sites/<int:site_id>", methods=["PUT"])
def update_dive_site(site_id):
    actor, error_response = require_auth()
    if error_response:
        return error_response

    payload = request.get_json(silent=True) or {}
    try:
        normalized = normalize_site_payload(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    site = store.update_site(site_id, normalized, actor)
    if not site:
        return jsonify({"error": "Dive site not found."}), 404
    return jsonify(site)

@app.route("/api/surveys")
def get_surveys():
    return jsonify(store.list_sites())

@app.route("/api/surveys/<int:survey_id>")
def get_survey(survey_id):
    survey = store.get_site(survey_id)
    if not survey:
        return jsonify({"error": "Not found"}), 404
    return jsonify(survey)

@app.route("/api/user")
def get_user():
    return jsonify(get_current_user())

if __name__ == "__main__":
    # In production, use a real server and handle HTTPS
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
