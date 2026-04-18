"""
Central configuration — all environment variable access lives here.
Import from this module instead of calling os.environ directly anywhere else.
"""
import os
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    """Return the value of a required env var, raising clearly if missing."""
    value = os.environ.get(key)
    if not value:
        raise EnvironmentError(
            f"Required environment variable '{key}' is not set. "
            "Check your .env file against .env.example."
        )
    return value


# Flask
FLASK_ENV = os.environ.get("FLASK_ENV", "production")
FLASK_DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
FLASK_SECRET_KEY = _require("FLASK_SECRET_KEY")

# Database
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///formcoach.db")

# JWT
JWT_SECRET_KEY = _require("JWT_SECRET_KEY")

# CORS
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

# OpenAI
OPENAI_API_KEY = _require("OPENAI_API_KEY")

# Butterbase
BUTTERBASE_API_KEY = _require("BUTTERBASE_API_KEY")
BUTTERBASE_APP_ID = _require("BUTTERBASE_APP_ID")
BUTTERBASE_API_BASE = os.environ.get("BUTTERBASE_API_BASE", "https://api.butterbase.ai")
BUTTERBASE_API_URL = f"{BUTTERBASE_API_BASE}/v1/{BUTTERBASE_APP_ID}"
BUTTERBASE_STORAGE_URL = f"{BUTTERBASE_API_BASE}/storage/{BUTTERBASE_APP_ID}"

# IonRouter
IONROUTER_API_KEY = _require("IONROUTER_API_KEY")

# Seadance
SEADANCE_API_KEY = _require("SEADANCE_API_KEY")

# Photon
PHOTON_API_KEY = _require("PHOTON_API_KEY")
PHOTON_WEBHOOK_SECRET = _require("PHOTON_WEBHOOK_SECRET")

# MiroMind
MIROMIND_API_KEY = _require("MIROMIND_API_KEY")
