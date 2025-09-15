import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- API Keys and Endpoints ---
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")
CEREBRAS_API_BASE = "https://api.cerebras.ai/v1"

# --- LLM Configuration ---
MODEL_NAME = "gpt-oss-120b"
MAX_COMPLETION_TOKENS = 65536
TEMPERATURE = 1.0
TOP_P = 1.0
REASONING_EFFORT = "medium"

# --- News Fetching Configuration ---
NEWS_TOPICS = [
    '"stock market"',
    '"artificial intelligence"',
    '"climate change"',
    '"biotechnology"',
]
NEWS_LANG = 'en'
NEWS_COUNTRY = 'US'
NEWS_FETCH_INTERVAL = 1  # seconds
WORKER_COUNT = 1


# --- FastAPI App Configuration ---
APP_TITLE = "Real-Time News Analysis API"
APP_DESCRIPTION = "An API that fetches news, analyzes it with an LLM, and streams results via WebSocket."
APP_VERSION = "2.0.0"

# --- CORS Configuration ---
ALLOWED_ORIGINS = ["*"]
