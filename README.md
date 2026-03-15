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

Fill `.env` with the Firebase web app config from Firebase Console:

- Project settings -> General -> Your apps -> Web app
- Authentication -> Sign-in method -> enable `Google`

Start the server:

```bash
python server.py
```

## Notes

- Google sign-in happens in the browser with Firebase Auth.
- Database writes are emulated in memory on the Flask server.
- `POST /api/dive-sites` and `PUT /api/dive-sites/<id>` require a Firebase ID token.
- The backend attributes each write by `email` when available, otherwise `sub`.
- The server auto-loads `.env` on startup for local development.
