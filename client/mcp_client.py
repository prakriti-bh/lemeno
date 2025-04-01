#!/usr/bin/env python3
import os
import sys
import time
import requests
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style
from prompt_toolkit.history import FileHistory
from pathlib import Path
import pyfiglet
from rich.console import Console
from rich.markdown import Markdown

from .config import SERVER_URL, LLM_PREFIX, HISTORY_FILE, CONFIG_DIR, PROMPT_MARKER
from .command_processor import CommandProcessor
from .llm_interface import LLMInterface

# Create config directory if it doesn't exist
if not os.path.exists(CONFIG_DIR):
    os.makedirs(CONFIG_DIR)

# Initialize console
console = Console()

# Initialize prompt style
style = Style.from_dict({
    "prompt": "#00aa00 bold",
    "path": "#0000aa",
})

def check_server_connection():
    """Check if the MCP server is running."""
    try:
        response = requests.get(f"{SERVER_URL}/api/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def print_welcome_banner():
    """Print a welcome banner."""
    ascii_banner = pyfiglet.figlet_format("MCP Terminal", font="slant")
    console.print(f"[bold green]{ascii_banner}[/bold green]")
    console.print("[bold]AI-Powered Terminal Assistant[/bold]")
    console.print("Type [bold cyan]@help[/bold cyan] for commands\n")

def get_prompt(current_dir):
    """Get the prompt with current directory."""
    username = os.environ.get("USER", "user")
    hostname = os.environ.get("HOSTNAME", "localhost")
    
    # Shorten home directory
    home = str(Path.home())
    if current_dir.startswith(home):
        current_dir = "~" + current_dir[len(home):]
    
    return HTML(f"<prompt>{username}@{hostname}</prompt>:<path>{current_dir}</path>{PROMPT_MARKER}")

def main():
    """Main function to run the MCP client."""
    print_welcome_banner()
    
    # Check server connection
    server_running = check_server_connection()
    if not server_running:
        console.print("[bold yellow]Warning: MCP server is not running.[/bold yellow]")
        console.print("[yellow]Some features will be limited. Start the server with: python server/mcp_server.py[/yellow]\n")
    
    # Initialize LLM interface
    llm = LLMInterface()
    
    # Initialize command processor
    processor = CommandProcessor(llm)
    
    # Initialize prompt session with history
    session = PromptSession(
        history=FileHistory(HISTORY_FILE),
        style=style
    )
    
    # Main loop
    while True:
        try:
            # Get user input
            user_input = session.prompt(
                lambda: get_prompt(processor.current_dir),
                complete_in_thread=True
            )
            
            # Process input
            command_type, command_value = processor.process_input(user_input)
            
            if command_type is None:
                continue
            
            # Handle different command types
            if command_type == "shell_command":
                stdout, stderr, exit_code = processor.execute_shell_command(command_value)
                
                if stdout:
                    console.print(stdout, end="")
                
                if stderr:
                    console.print(f"[red]{stderr}[/red]", end="")
            
            elif command_type == "change_directory":
                success, message = processor.change_directory(command_value)
                
                if not success:
                    console.print(f"[red]{message}[/red]")
            
            elif command_type == "llm_query":
                if not server_running:
                    server_running = check_server_connection()
                
                success, response = processor.handle_llm_query(command_value)
                
                if not success:
                    console.print(f"[red]{response}[/red]")
            
            elif command_type == "index_project":
                success, message = processor.index_current_project(command_value)
                
                if success:
                    console.print(f"[green]{message}[/green]")
                else:
                    console.print(f"[red]{message}[/red]")
            
            elif command_type == "status":
                success, message = processor.get_indexing_status()
                
                if success:
                    console.print(f"[blue]{message}[/blue]")
                else:
                    console.print(f"[red]{message}[/red]")
            
            elif command_type == "history":
                success, message = processor.get_command_history(command_value)
                
                if success:
                    console.print(f"[blue]{message}[/blue]")
                else:
                    console.print(f"[red]{message}[/red]")
            
            elif command_type == "help":
                success, message = processor.show_help()
                console.print(message)
        
        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            console.print("\n[yellow]Use Ctrl+D to exit[/yellow]")
        
        except EOFError:
            # Handle Ctrl+D to exit
            console.print("\n[green]Goodbye![/green]")
            break
        
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

if __name__ == "__main__":
    main()