import os
import subprocess
import requests
import json
from .config import SERVER_URL, LLM_PREFIX

class CommandProcessor:
    def __init__(self, llm_interface=None):
        self.server_url = SERVER_URL
        self.llm_interface = llm_interface
        self.current_dir = os.getcwd()
    
    def process_input(self, user_input):
        """Process user input and determine how to handle it."""
        if not user_input.strip():
            return None, None
        
        # Handle LLM query
        if user_input.startswith(LLM_PREFIX):
            query = user_input[len(LLM_PREFIX):].strip()
            return "llm_query", query
        
        # Handle special commands
        if user_input.startswith("@index"):
            path = user_input[7:].strip() or os.getcwd()
            return "index_project", path
        
        if user_input.startswith("@help"):
            return "help", None
        
        if user_input.startswith("@status"):
            return "status", None
        
        if user_input.startswith("@history"):
            limit = 10
            try:
                parts = user_input.split()
                if len(parts) > 1:
                    limit = int(parts[1])
            except ValueError:
                pass
            return "history", limit
        
        # Handle directory change (needs special handling)
        if user_input.startswith("cd "):
            directory = user_input[3:].strip()
            return "change_directory", directory
        
        # Handle all other commands as shell commands
        return "shell_command", user_input
    
    def execute_shell_command(self, command):
        """Execute a shell command and return the output."""
        try:
            # Log the command via the server
            response = requests.post(
                f"{self.server_url}/api/command/execute",
                json={
                    "command": command,
                    "working_dir": self.current_dir
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("output", ""), result.get("error", ""), result.get("exit_code", 1)
            else:
                # Fallback to local execution if server fails
                process = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=self.current_dir
                )
                return process.stdout, process.stderr, process.returncode
        
        except requests.exceptions.ConnectionError:
            # Fallback to local execution if server is down
            process = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.current_dir
            )
            return process.stdout, process.stderr, process.returncode
        
        except Exception as e:
            return "", f"Error executing command: {e}", 1
    
    def change_directory(self, directory):
        """Change the current working directory."""
        try:
            # Handle home directory
            if directory == "~" or directory.startswith("~/"):
                directory = os.path.expanduser(directory)
            
            # Handle relative paths
            if not os.path.isabs(directory):
                directory = os.path.join(self.current_dir, directory)
            
            # Check if directory exists
            if not os.path.isdir(directory):
                return False, f"Directory not found: {directory}"
            
            # Change directory
            self.current_dir = os.path.abspath(directory)
            os.chdir(self.current_dir)
            
            # Log the command
            try:
                requests.post(
                    f"{self.server_url}/api/command/log",
                    json={
                        "command": f"cd {directory}",
                        "output": "",
                        "working_dir": self.current_dir,
                        "exit_code": 0
                    }
                )
            except:
                # Continue even if logging fails
                pass
            
            return True, f"Changed directory to: {self.current_dir}"
        
        except Exception as e:
            return False, f"Error changing directory: {e}"
    
    def handle_llm_query(self, query):
        """Handle a query to the LLM."""
        if not self.llm_interface:
            return False, "LLM interface not initialized"
        
        try:
            # Get context from the server
            response = requests.post(
                f"{self.server_url}/api/context/generate",
                json={
                    "query": query,
                    "project_path": self.current_dir
                }
            )
            
            if response.status_code == 200:
                context = response.json().get("context", {})
                
                # Generate response from LLM
                llm_response = self.llm_interface.generate_response(query, context, stream=True)
                
                return True, llm_response
            else:
                # Fallback to querying without context
                llm_response = self.llm_interface.generate_response(query, None, stream=True)
                
                return True, llm_response
        
        except requests.exceptions.ConnectionError:
            # Fallback to querying without context if server is down
            llm_response = self.llm_interface.generate_response(query, None, stream=True)
            
            return True, llm_response
        
        except Exception as e:
            return False, f"Error handling LLM query: {e}"
    
    def index_current_project(self, path=None):
        """Index the current project or a specified path."""
        project_path = path or self.current_dir
        
        try:
            response = requests.post(
                f"{self.server_url}/api/index/project",
                json={"project_path": project_path}
            )
            
            if response.status_code == 200:
                return True, f"Started indexing: {project_path}"
            else:
                return False, f"Failed to start indexing: {response.text}"
        
        except requests.exceptions.ConnectionError:
            return False, "Server is not running. Start the server first."
        
        except Exception as e:
            return False, f"Error indexing project: {e}"
    
    def get_indexing_status(self):
        """Get the current indexing status."""
        try:
            response = requests.get(f"{self.server_url}/api/index/status")
            
            if response.status_code == 200:
                status = response.json()
                
                if status.get("is_indexing"):
                    return True, f"Indexing in progress: {status.get('project')}\nIndexed files: {status.get('indexed_files')}, Queue size: {status.get('queue_size')}"
                else:
                    return True, "No indexing in progress"
            else:
                return False, f"Failed to get indexing status: {response.text}"
        
        except requests.exceptions.ConnectionError:
            return False, "Server is not running. Start the server first."
        
        except Exception as e:
            return False, f"Error getting indexing status: {e}"
    
    def get_command_history(self, limit=10):
        """Get recent command history."""
        try:
            response = requests.post(
                f"{self.server_url}/api/search/commands",
                json={"query": "", "limit": limit}
            )
            
            if response.status_code == 200:
                commands = response.json().get("results", [])
                
                if not commands:
                    return True, "No command history found"
                
                history_text = "Recent commands:\n"
                for i, cmd in enumerate(commands, 1):
                    history_text += f"{i}. {cmd.get('command')}\n"
                
                return True, history_text.strip()
            else:
                return False, f"Failed to get command history: {response.text}"
        
        except requests.exceptions.ConnectionError:
            return False, "Server is not running. Start the server first."
        
        except Exception as e:
            return False, f"Error getting command history: {e}"
    
    def show_help(self):
        """Show help information."""
        help_text = """
MCP Terminal Assistant - Help
=============================

Commands:
  @llm <query>          - Ask the AI assistant (e.g., @llm how to check disk space)
  @index [path]         - Index the current directory or specified path
  @status               - Check indexing status
  @history [limit]      - Show recent command history (default: 10)
  @help                 - Show this help message

The assistant can:
  - Answer questions about your codebase
  - Explain shell commands
  - Suggest commands for specific tasks
  - Help debug issues
  - Provide code examples
  
All commands and their outputs are stored to provide context for future queries.
        """
        return True, help_text.strip()