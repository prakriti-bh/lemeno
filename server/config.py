import os
from pathlib import Path

# Server configuration
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5000

# Database configuration
DB_FILE = os.path.join(Path.home(), ".mcp_terminal", "session_history.db")
DB_DIR = os.path.dirname(DB_FILE)

# Ensure the directory exists
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

# Code indexing configuration
MAX_CODE_RESULTS = 10
IGNORED_DIRS = [
    ".git", "__pycache__", "node_modules", "venv", 
    "env", ".venv", ".env", "build", "dist"
]
INDEXED_EXTENSIONS = [
    ".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs",
    ".cpp", ".c", ".h", ".hpp", ".java", ".php", ".rb",
    ".html", ".css", ".scss", ".json", ".yml", ".yaml",
    ".md", ".sh", ".bash", ".zsh", ".sql"
]

# Ollama configuration
OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "deepseek-coder:33b-instruct-q5_K_M"

# Aider configuration
AIDER_CONFIG_DIR = os.path.join(Path.home(), ".aider")