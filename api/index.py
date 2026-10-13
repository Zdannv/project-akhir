"""Titik masuk Vercel: seluruh /api/* dilayani aplikasi FastAPI yang sama
dengan yang dijalankan secara lokal (backend/app/main.py)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.main import app  # noqa: E402,F401
