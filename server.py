import os
from copy import deepcopy
from datetime import datetime, timezone
from flask import Flask, jsonify, render_template, request, url_for, session, redirect
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

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

# --- In-Memory Store (formerly app/store.py) ---

def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

class DiveSiteStore:
    def __init__(self):
        seed_user = {
            "email": "seed@tide.local",
            "sub": "seed-user",
            "display_name": "TIDE Seed Data",
            "identifier": "seed@tide.local",
        }
        self._sites = [
            {
                "id": 1,
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
                "added_by": seed_user,
                "updated_by": seed_user,
            },
            {
                "id": 2,
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
                "added_by": seed_user,
                "updated_by": seed_user,
            },
            {
                "id": 3,
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
                "added_by": seed_user,
                "updated_by": seed_user,
            },
            {
                "id": 4,
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
                "added_by": seed_user,
                "updated_by": seed_user,
            },
        ]
        self._next_id = len(self._sites) + 1

    def list_sites(self):
        return deepcopy(self._sites)

    def get_site(self, site_id):
        site = next((site for site in self._sites if site["id"] == site_id), None)
        return deepcopy(site) if site else None

    def create_site(self, payload, actor):
        timestamp = now_iso()
        site = {
            "id": self._next_id,
            **payload,
            "added_at": timestamp,
            "updated_at": timestamp,
            "added_by": actor,
            "updated_by": actor,
        }
        self._sites.append(site)
        self._next_id += 1
        return deepcopy(site)

    def update_site(self, site_id, payload, actor):
        site = next((site for site in self._sites if site["id"] == site_id), None)
        if not site:
            return None

        site.update(payload)
        site["updated_at"] = now_iso()
        site["updated_by"] = actor
        return deepcopy(site)

store = DiveSiteStore()

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
