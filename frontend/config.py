import os
from dotenv import load_dotenv

load_dotenv()

# Backend FastAPI URL — override via BACKEND_URL env var for Docker / prod
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_BASE = f"{BACKEND_URL}/api"

# App identity
APP_NAME = "MenuMind"
APP_ICON = "🍽️"
APP_TAGLINE = "AI-Powered Restaurant Personalization"

# UI constants
PRIMARY_COLOR = "#E8491D"       # warm brand orange
SECONDARY_COLOR = "#1A1A2E"     # dark navy
ACCENT_COLOR = "#F5A623"        # golden accent
SUCCESS_COLOR = "#27AE60"
ERROR_COLOR = "#E74C3C"
