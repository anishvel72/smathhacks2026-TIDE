import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - startup still works without dotenv
    def load_dotenv(*_args, **_kwargs):
        return False


BASE_DIR = Path(__file__).resolve().parent.parent


def load_settings():
    load_dotenv(BASE_DIR / ".env")
    return {
        "firebase": {
            "apiKey": os.environ.get("FIREBASE_API_KEY", ""),
            "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN", ""),
            "projectId": os.environ.get("FIREBASE_PROJECT_ID", ""),
            "storageBucket": os.environ.get("FIREBASE_STORAGE_BUCKET", ""),
            "messagingSenderId": os.environ.get("FIREBASE_MESSAGING_SENDER_ID", ""),
            "appId": os.environ.get("FIREBASE_APP_ID", ""),
        }
    }
