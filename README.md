# TIDE

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a local `.env` from the example:

```bash
cp .env.example .env
```

Fill `.env` with the app secrets:

- `FLASK_SECRET_KEY`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- Optional: `DATABASE_PATH` to override the default local SQLite file (`tide.db`)

Start the server:

```bash
python server.py
```

## Notes

- Google sign-in happens through the Flask OAuth flow.
- Dive-site data persists in a local SQLite database.
- `POST /api/dive-sites` and `PUT /api/dive-sites/<id>` require an authenticated session.
- The backend attributes each write by `email` when available, otherwise `sub`.
- The server auto-loads `.env` on startup and creates the SQLite schema with seed data on first launch.
