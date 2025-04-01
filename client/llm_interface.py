import requests
import json
import os
import time
from .config import OLLAMA_URL, DEFAULT_MODEL, SYSTEM_PROMPT

class LLMInterface:
    def __init__(self, model=DEFAULT_MODEL):
        self.model = model
        self.base_url = OLLAMA_URL
        self.check_ollama_availability()
    
    def check_ollama_availability(self):
        """Check if Ollama server is running."""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                available_models = response.json().get("models", [])
                model_names = [model.get("name") for model in available_models]
                
                if self.model not in model_names:
                    print(f"Warning: Model '{self.model}' not found in Ollama. Available models: {', '.join(model_names)}")
                    print(f"Trying to pull model '{self.model}'...")
                    self._pull_model()
            
            return True
        except requests.exceptions.ConnectionError:
            print("Error: Cannot connect to Ollama server. Please ensure Ollama is running.")
            return False
    
    def _pull_model(self):
        """Pull the model if not available."""
        try:
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": self.model}
            )
            
            if response.status_code == 200:
                print(f"Successfully pulled model '{self.model}'")
                return True
            else:
                print(f"Failed to pull model '{self.model}': {response.text}")
                return False
        except Exception as e:
            print(f"Error pulling model: {e}")
            return False
    
    def generate_response(self, query, context=None, stream=False):
        """Generate a response from the LLM."""
        # Build messages
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        
        # Add context if provided
        if context:
            context_str = self._format_context(context)
            messages.append({"role": "system", "content": context_str})
        
        # Add user query
        messages.append({"role": "user", "content": query})
        
        # Make the API call
        try:
            if stream:
                return self._stream_response(messages)
            else:
                return self._get_response(messages)
        except Exception as e:
            return f"Error: Failed to get a response from the LLM: {e}"
    
    def _format_context(self, context):
        """Format the context for the LLM."""
        context_parts = []
        
        # Add project path
        if "project_path" in context:
            context_parts.append(f"Current project: {context['project_path']}")
        
        # Add code snippets
        if "code_snippets" in context and context["code_snippets"]:
            context_parts.append("Relevant code snippets:")
            for i, snippet in enumerate(context["code_snippets"], 1):
                file_path = snippet.get("file_path", "unknown")
                content = snippet.get("content", "")
                language = snippet.get("language", "")
                
                # Truncate long snippets
                if len(content) > 500:
                    content = content[:500] + "... [truncated]"
                
                context_parts.append(f"Snippet {i} from {file_path} ({language}):")
                context_parts.append(f"```{language}\n{content}\n```")
        
        # Add command history
        if "command_history" in context and context["command_history"]:
            context_parts.append("Relevant command history:")
            for i, cmd in enumerate(context["command_history"], 1):
                command = cmd.get("command", "")
                output = cmd.get("output", "")
                
                # Truncate long outputs
                if len(output) > 200:
                    output = output[:200] + "... [truncated]"
                
                context_parts.append(f"Command {i}: {command}")
                if output:
                    context_parts.append(f"Output: {output}")
        
        return "\n\n".join(context_parts)
    
    def _get_response(self, messages):
        """Get a response from the LLM."""
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": False
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("message", {}).get("content", "No response")
        else:
            return f"Error: {response.status_code} - {response.text}"
    
    def _stream_response(self, messages):
        """Stream a response from the LLM."""
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": True
            },
            stream=True
        )
        
        full_response = ""
        
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            print(content, end="", flush=True)
                            full_response += content
                    except json.JSONDecodeError:
                        pass
            
            print()  # New line at end
            return full_response
        else:
            error_msg = f"Error: {response.status_code} - {response.text}"
            print(error_msg)
            return error_msg