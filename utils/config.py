import os

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))

# --- llama.cpp server -----------------------------------------------------------
LLAMA_HOST = os.environ.get("LLAMA_HOST", "http://127.0.0.1:8033")
LLAMA_CHAT_ENDPOINT = f"{LLAMA_HOST}/v1/chat/completions"
LLAMA_EMBED_ENDPOINT = f"{LLAMA_HOST}/v1/embeddings"

# --- Model tuning ---------------------------------------------------------------
EMBED_DIM = int(os.environ.get("EMBED_DIM", "1536"))
REQUEST_TIMEOUT = float(os.environ.get("BP_TIMEOUT", "60"))
EMBED_TIMEOUT = float(os.environ.get("BP_EMBED_TIMEOUT", "90"))
CHAT_TEMPERATURE = 0.2
CHAT_MAX_TOKENS = 512

# --- Local storage --------------------------------------------------------------
DATA_DIR = os.environ.get("BP_DATA_DIR", ROOT_DIR)
TASKS_FILE = os.path.join(DATA_DIR, "tasks.json")
VEC_DB_PATH = os.path.join(DATA_DIR, "vectors.db")
DOCUMENTS_DIR = os.path.join(DATA_DIR, "documents")

os.makedirs(DOCUMENTS_DIR, exist_ok=True)

# --- Scheduler ------------------------------------------------------------------
CHECK_INTERVAL_SECONDS = 60

# --- RAG ------------------------------------------------------------------------
RAG_TOP_K = 3
RAG_CHUNK_SIZE = 400

# --- Context window ------------------------------------------------------------
MAX_PROMPT_CHARS = 1800  # ~1200 tokens, safe within 2048 ctx (-c 2048)
MAX_HISTORY_TURNS = 4     # only last N exchanges sent to model

# --- Defaults -------------------------------------------------------------------
DEFAULT_SYSTEM_PROMPT = "You are a helpful business assistant."
