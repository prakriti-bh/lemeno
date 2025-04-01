import os
from pathlib import Path

# Server configuration
SERVER_URL = "http://127.0.0.1:5000"

# Ollama configuration
OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "deepseek-coder:33b-instruct-q5_K_M"

# Client configuration
HISTORY_FILE = os.path.join(Path.home(), ".mcp_terminal", "client_history.txt")
CONFIG_DIR = os.path.dirname(HISTORY_FILE)

# Ensure the directory exists
if not os.path.exists(CONFIG_DIR):
    os.makedirs(CONFIG_DIR)

# Command prefix for LLM queries
LLM_PREFIX = "@llm"

# System prompt for LLM
SYSTEM_PROMPT = """
You are an AI terminal assistant for developers. You have access to:
1. The current project's codebase
2. The user's command history
3. The current working directory

Help the user by:
- Explaining commands
- Suggesting terminal commands for tasks
- Providing code snippets
- Debugging issues
- Offering workflow improvements

Be concise and practical in your responses.
"""

# Tool descriptions
TOOL_DESCRIPTIONS = {
    "search_code": "Search the codebase for specific patterns or code",
    "get_commands": "Retrieve similar commands from history",
    "execute_command": "Execute a shell command",
    "index_project": "Index a project directory for code context"
}

# Maximum command history to display
MAX_HISTORY_DISPLAY = 10

# UI configuration
PROMPT_MARKER = "$ "
RESPONSE_COLOR = "green"
ERROR_COLOR = "red"
INFO_COLOR = "blue"