import os
import fnmatch
from pathlib import Path
import time
import threading
from queue import Queue
from .database import add_code_file
from .config import IGNORED_DIRS, INDEXED_EXTENSIONS

class CodeIndexer:
    def __init__(self):
        self.index_queue = Queue()
        self.indexing_thread = None
        self.is_indexing = False
        self.current_project = None
        self.indexed_files_count = 0
        
    def start_indexing_thread(self):
        """Start the background indexing thread."""
        if self.indexing_thread is None or not self.indexing_thread.is_alive():
            self.indexing_thread = threading.Thread(
                target=self._process_index_queue,
                daemon=True
            )
            self.indexing_thread.start()
    
    def _process_index_queue(self):
        """Process files in the index queue."""
        while True:
            try:
                file_path = self.index_queue.get(timeout=1)
                self._index_file(file_path)
                self.index_queue.task_done()
                self.indexed_files_count += 1
            except Exception as e:
                # Empty queue or error
                if self.index_queue.empty():
                    self.is_indexing = False
                time.sleep(0.1)
    
    def _index_file(self, file_path):
        """Index a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Determine language from file extension
            _, ext = os.path.splitext(file_path)
            language = ext[1:] if ext else ""
            
            # Add to database
            add_code_file(file_path, content, language)
            return True
        except Exception as e:
            print(f"Error indexing {file_path}: {e}")
            return False
    
    def should_index_file(self, file_path):
        """Check if a file should be indexed based on extension and ignore patterns."""
        # Check if file extension is in our list of indexed extensions
        _, ext = os.path.splitext(file_path)
        if ext.lower() not in INDEXED_EXTENSIONS:
            return False
        
        # Check if file is in an ignored directory
        for ignored_dir in IGNORED_DIRS:
            if ignored_dir in Path(file_path).parts:
                return False
        
        return True
    
    def index_project(self, project_path):
        """Index all files in a project directory."""
        project_path = os.path.abspath(project_path)
        self.current_project = project_path
        self.is_indexing = True
        self.indexed_files_count = 0
        
        # Start the indexing thread if not already running
        self.start_indexing_thread()
        
        # Walk through the project directory
        for root, dirs, files in os.walk(project_path):
            # Remove ignored directories from dirs to prevent walking them
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            
            for file in files:
                file_path = os.path.join(root, file)
                if self.should_index_file(file_path):
                    self.index_queue.put(file_path)
        
        return True
    
    def get_indexing_status(self):
        """Get the current indexing status."""
        return {
            "is_indexing": self.is_indexing,
            "project": self.current_project,
            "indexed_files": self.indexed_files_count,
            "queue_size": self.index_queue.qsize()
        }

# Global indexer instance
indexer = CodeIndexer()