from pathlib import Path

from flask import Flask

from .config import load_settings
from .routes import register_routes
from .store import DiveSiteStore


BASE_DIR = Path(__file__).resolve().parent.parent


def create_app():
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
    )
    app.config["TIDE_SETTINGS"] = load_settings()
    app.config["DIVE_SITE_STORE"] = DiveSiteStore()
    register_routes(app)
    return app
