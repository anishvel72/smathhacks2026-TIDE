from flask import current_app, jsonify, render_template, request

from .auth import require_actor


def normalize_site_payload(payload):
    required_fields = [
        "name",
        "region",
        "difficulty",
        "notes",
        "lat",
        "lng",
        "depth_ft",
        "visibility_ft",
    ]
    missing = [field for field in required_fields if field not in payload]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

    normalized = {
        "name": str(payload["name"]).strip(),
        "region": str(payload["region"]).strip(),
        "difficulty": str(payload["difficulty"]).strip(),
        "notes": str(payload["notes"]).strip(),
        "lat": float(payload["lat"]),
        "lng": float(payload["lng"]),
        "depth_ft": int(payload["depth_ft"]),
        "visibility_ft": int(payload["visibility_ft"]),
    }

    if not normalized["name"]:
        raise ValueError("Name is required.")
    if not normalized["region"]:
        raise ValueError("Region is required.")
    if not (-90 <= normalized["lat"] <= 90):
        raise ValueError("Latitude must be between -90 and 90.")
    if not (-180 <= normalized["lng"] <= 180):
        raise ValueError("Longitude must be between -180 and 180.")
    if normalized["depth_ft"] < 0 or normalized["visibility_ft"] < 0:
        raise ValueError("Depth and visibility must be non-negative.")

    return normalized


def register_routes(app):
    @app.route("/")
    def index():
        return render_template("index.html", firebase_config=app.config["TIDE_SETTINGS"]["firebase"])

    @app.route("/api/firebase-config")
    def get_firebase_config():
        return jsonify(app.config["TIDE_SETTINGS"]["firebase"])

    @app.route("/api/dive-sites")
    def get_dive_sites():
        store = current_app.config["DIVE_SITE_STORE"]
        return jsonify(store.list_sites())

    @app.route("/api/dive-sites/<int:site_id>")
    def get_dive_site(site_id):
        store = current_app.config["DIVE_SITE_STORE"]
        site = store.get_site(site_id)
        if not site:
            return jsonify({"error": "Dive site not found."}), 404
        return jsonify(site)

    @app.route("/api/dive-sites", methods=["POST"])
    def create_dive_site():
        actor, error_response = require_actor()
        if error_response:
            return error_response

        payload = request.get_json(silent=True) or {}
        try:
            normalized = normalize_site_payload(payload)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        store = current_app.config["DIVE_SITE_STORE"]
        site = store.create_site(normalized, actor)
        return jsonify(site), 201

    @app.route("/api/dive-sites/<int:site_id>", methods=["PUT"])
    def update_dive_site(site_id):
        actor, error_response = require_actor()
        if error_response:
            return error_response

        payload = request.get_json(silent=True) or {}
        try:
            normalized = normalize_site_payload(payload)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        store = current_app.config["DIVE_SITE_STORE"]
        site = store.update_site(site_id, normalized, actor)
        if not site:
            return jsonify({"error": "Dive site not found."}), 404
        return jsonify(site)

    @app.route("/api/surveys")
    def get_surveys():
        store = current_app.config["DIVE_SITE_STORE"]
        return jsonify(store.list_sites())

    @app.route("/api/surveys/<int:survey_id>")
    def get_survey(survey_id):
        store = current_app.config["DIVE_SITE_STORE"]
        survey = store.get_site(survey_id)
        if not survey:
            return jsonify({"error": "Not found"}), 404
        return jsonify(survey)
