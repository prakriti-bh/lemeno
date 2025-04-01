#!/bin/bash

# ANSI color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Setting up MCP Terminal Assistant...${NC}"

# Create directory structure
mkdir -p server
mkdir -p client

# Install Python requirements
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install -r requirements.txt

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo -e "${YELLOW}Installing Ollama...${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew install ollama
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        curl -fsSL https://ollama.com/install.sh | sh
    else
        echo "Please install Ollama manually from: https://ollama.com/download"
    fi
else
    echo -e "${GREEN}Ollama is already installed.${NC}"
fi

# Pull DeepSeek-Coder model
echo -e "${YELLOW}Pulling DeepSeek-Coder model (this may take a while)...${NC}"
ollama pull deepseek-coder:33b-instruct-q5_K_M

# Initialize the SQLite database
echo -e "${YELLOW}Initializing database...${NC}"
python -c "from server.database import init_db; init_db()"

echo -e "${GREEN}Setup complete! Run the server with: python server/mcp_server.py${NC}"
echo -e "${GREEN}Then run the client with: python client/mcp_client.py${NC}"