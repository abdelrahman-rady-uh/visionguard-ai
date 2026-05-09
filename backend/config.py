import os

# Load .env before reading any os.getenv() values so local dev credentials work.
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
except ImportError:
    pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join(BASE_DIR, "uploads"))
RESULTS_DIR = os.getenv("RESULTS_DIR", os.path.join(BASE_DIR, "results"))
DATABASE_PATH = os.getenv("DATABASE_PATH", os.path.join(BASE_DIR, "database", "app.db"))
LOG_PATH = os.getenv("LOG_PATH", os.path.join(BASE_DIR, "logs"))
SECRET_KEY_PATH = os.getenv("SECRET_KEY_PATH", os.path.join(BASE_DIR, "backend", "aes.key"))
ALLOWED_EXTENSIONS = {"mp4", "avi", "mov"}
MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 1024 * 1024 * 1024))

# Flask session secret key
SECRET_KEY = os.getenv("SECRET_KEY", "visionguard-dev-key-change-in-production-min-32-chars")

# Google OAuth 2.0 credentials — set these in .env
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://127.0.0.1:5000/auth/callback")
