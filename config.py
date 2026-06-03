import os
from dotenv import load_dotenv

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
_ROOT = os.path.dirname(os.path.abspath(__file__))
RAG_INDEX_DIR = os.path.join(_ROOT, "rag", "index")
RAG_DATA_DIR = os.path.join(_ROOT, "rag", "data")

TOP_K_DEFAULT = 5
PROMPT_GEN_MAX_COUNT = 10
