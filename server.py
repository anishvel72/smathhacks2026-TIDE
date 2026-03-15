from flask import Flask, jsonify, render_template
from datetime import date

app = Flask(__name__)

# In-memory mock data for now — swap with DB queries later
SURVEYS = [
    { "id": 1, "lat": 25.0097, "lng": -80.3762, "name": "Molasses Reef", "org": "NOAA",                 "date": "2025-02-15", "cert_required": "Open Water", "capacity": 8,  "divers_joined": 3 },
    { "id": 2, "lat": 25.0255, "lng": -80.3529, "name": "French Reef",   "org": "Reef Check",           "date": "2025-02-18", "cert_required": "Open Water", "capacity": 6,  "divers_joined": 6 },
    { "id": 3, "lat": 24.6266, "lng": -81.1102, "name": "Sombrero Reef", "org": "Coral Restoration",    "date": "2025-02-20", "cert_required": "Advanced",   "capacity": 10, "divers_joined": 1 },
    { "id": 4, "lat": 24.5481, "lng": -81.4068, "name": "Looe Key",      "org": "FKNMS",                "date": "2025-02-22", "cert_required": "Open Water", "capacity": 8,  "divers_joined": 0 },
]

@app.route("/")
def index():
    return render_template("./index.html")

@app.route("/api/surveys")
def get_surveys():
    return jsonify(SURVEYS)

@app.route("/api/surveys/<int:survey_id>")
def get_survey(survey_id):
    survey = next((s for s in SURVEYS if s["id"] == survey_id), None)
    if not survey:
        return jsonify({ "error": "Not found" }), 404
    return jsonify(survey)

if __name__ == "__main__":
    app.run(debug=True)