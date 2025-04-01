#!/usr/bin/env python3
import os
import sys
import subprocess
import time
import signal
import argparse

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run MCP Terminal Assistant")
    parser.add_argument("--server-only", action="store_true", help="Run only the server")
    parser.add_argument("--client-only", action="store_true", help="Run only the client")
    return parser.parse_args()

def run_server():
    """Run the MCP server process."""
    server_process = subprocess.Popen(
        [sys.executable, "-m", "server.mcp_server"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    print("MCP Server started with PID:", server_process.pid)
    return server_process

def run_client():
    """Run the MCP client process."""
    client_process = subprocess.Popen(
        [sys.executable, "-m", "client.mcp_client"]
    )
    return client_process

def main():
    """Main function to run both server and client."""
    args = parse_args()
    
    server_process = None
    client_process = None
    
    try:
        # Run server if not client-only
        if not args.client_only:
            server_process = run_server()
            # Give the server time to start
            time.sleep(2)
        
        # Run client if not server-only
        if not args.server_only:
            client_process = run_client()
            client_process.wait()
    
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt. Shutting down...")
    
    finally:
        # Clean up processes
        if client_process and client_process.poll() is None:
            client_process.terminate()
            client_process.wait()
            print("Client process terminated")
        
        if server_process and server_process.poll() is None:
            server_process.terminate()
            server_process.wait()
            print("Server process terminated")
            
            # Print server output for debugging
            stdout, stderr = server_process.communicate()
            if stderr:
                print("Server errors:", stderr)

if __name__ == "__main__":
    main()