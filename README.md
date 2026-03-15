# TIDE: Tracking and Intelligence for Diving Expeditions

**SMathHacks 2026 - Interface Design Track**

TIDE is a live, interactive atlas of the diving world designed for coordinated reef exploration and environmental reporting. Built for the **SMathHacks 2026 Interface Design track**, it focuses on a highly responsive, "zero-framework" frontend that prioritizes speed and visual clarity.

## Key Features

- **Live Dive Atlas**: Real-time rendering of dive sites using **Leaflet.js** with custom data overlays.
- **Unified Identity**: Seamless **Google OAuth** authentication via Authlib—stripping away complex platform overhead for a streamlined login experience.
- **Attributed Contributions**: Every site addition or update is verified and attributed to a real-world identity.
- **Intelligent Context**: Coordinate normalization and placeholders to ensure high-quality environmental data entry.
- **Ultra-Lean Architecture**: The entire backend logic is consolidated into a single, high-performance `server.py` file.

## Tech Stack

- **Frontend**: Vanilla JavaScript & CSS (Modern Glassmorphism), Leaflet.js Mapping.
- **Backend**: Python 3 / Flask (Consolidated Server).
- **Security**: Authlib (Google OAuth Integration).
- **Persistence**: Local SQLite Database.

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   Create a `.env` file from the provided example:
   ```bash
   cp .env.example .env
   ```
   Fill in your Google OAuth credentials and a Flask secret key:
   - `FLASK_SECRET_KEY`
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`

3. **Start the Server**:
   ```bash
   python server.py
   ```

## Development History

TIDE was refactored and refined during SMathHacks 2026 to transition from a distributed architecture to a high-performance single-file backend, emphasizing "Interface Design" through clean, responsive, and secure interaction patterns.
