import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import json
import time
from pathlib import Path

from server.database import (
    init_db, log_command, get_similar_commands, 
    search_code, update_project_history, get_recent_projects
)
from server.code_indexer import indexer
from server.config import SERVER_HOST, SERVER_PORT

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Ensure database is initialized
init_db()

# Start the indexer thread
indexer.start_indexing_thread()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "timestamp": time.time()
    })

@app.route('/api/index/project', methods=['POST'])
def index_project():
    """Index a project directory."""
    data = request.json
    project_path = data.get('project_path')
    
    if not project_path or not os.path.isdir(project_path):
        return jsonify({
            "status": "error",
            "message": "Invalid project path"
        }), 400
    
    # Update project history
    update_project_history(project_path)
    
    # Start indexing the project
    success = indexer.index_project(project_path)
    
    return jsonify({
        "status": "success" if success else "error",
        "message": "Indexing started" if success else "Failed to start indexing"
    })

@app.route('/api/index/status', methods=['GET'])
def indexing_status():
    """Get the current indexing status."""
    status = indexer.get_indexing_status()
    return jsonify(status)

@app.route('/api/search/code', methods=['POST'])
def search_codebase():
    """Search the indexed codebase."""
    data = request.json
    query = data.get('query')
    limit = data.get('limit', 10)
    
    if not query:
        return jsonify({
            "status": "error",
            "message": "Query is required"
        }), 400
    
    results = search_code(query, limit)
    
    return jsonify({
        "status": "success",
        "results": results
    })

@app.route('/api/search/commands', methods=['POST'])
def search_commands():
    """Search command history."""
    data = request.json
    query = data.get('query')
    limit = data.get('limit', 5)
    
    if not query:
        return jsonify({
            "status": "error",
            "message": "Query is required"
        }), 400
    
    results = get_similar_commands(query, limit)
    
    return jsonify({
        "status": "success",
        "results": results
    })

@app.route('/api/command/log', methods=['POST'])
def log_command_endpoint():
    """Log a command and its output."""
    data = request.json
    command = data.get('command')
    output = data.get('output', '')
    working_dir = data.get('working_dir', os.getcwd())
    exit_code = data.get('exit_code', 0)
    
    if not command:
        return jsonify({
            "status": "error",
            "message": "Command is required"
        }), 400
    
    success = log_command(command, output, working_dir, exit_code)
    
    return jsonify({
        "status": "success" if success else "error",
        "message": "Command logged" if success else "Failed to log command"
    })

@app.route('/api/command/execute', methods=['POST'])
def execute_command():
    """Execute a shell command and return the output."""
    data = request.json
    command = data.get('command')
    working_dir = data.get('working_dir', os.getcwd())
    
    if not command:
        return jsonify({
            "status": "error",
            "message": "Command is required"
        }), 400
    
    try:
        # Execute the command
        process = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=working_dir
        )
        
        # Log the command
        log_command(
            command,
            process.stdout + process.stderr,
            working_dir,
            process.returncode
        )
        
        return jsonify({
            "status": "success",
            "output": process.stdout,
            "error": process.stderr,
            "exit_code": process.returncode
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/projects/recent', methods=['GET'])
def recent_projects():
    """Get recently accessed projects."""
    limit = request.args.get('limit', 5, type=int)
    projects = get_recent_projects(limit)
    
    return jsonify({
        "status": "success",
        "projects": projects
    })

@app.route('/api/context/generate', methods=['POST'])
def generate_context():
    """Generate context for an LLM query."""
    data = request.json
    query = data.get('query')
    project_path = data.get('project_path', os.getcwd())
    
    if not query:
        return jsonify({
            "status": "error",
            "message": "Query is required"
        }), 400
    
    # Get relevant code snippets
    code_results = search_code(query, limit=5)
    
    # Get relevant commands
    command_results = get_similar_commands(query, limit=3)
    
    # Update project history
    update_project_history(project_path)
    
    # Format the context
    context = {
        "project_path": project_path,
        "code_snippets": code_results,
        "command_history": command_results,
        "timestamp": time.time()
    }
    
    return jsonify({
        "status": "success",
        "context": context
    })

if __name__ == '__main__':
    # Print some info
    print(f"Starting MCP Server on {SERVER_HOST}:{SERVER_PORT}")
    print("Press Ctrl+C to exit")
    
    # Start the server
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=True)