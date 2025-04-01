import sqlite3
import os
import time
from pathlib import Path
from .config import DB_FILE, DB_DIR

def get_db_connection():
    """Get a connection to the SQLite database."""
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)
    
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with the required tables."""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Command history table
    c.execute('''
    CREATE TABLE IF NOT EXISTS command_history (
        id INTEGER PRIMARY KEY,
        command TEXT NOT NULL,
        output TEXT,
        working_dir TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        exit_code INTEGER
    )
    ''')
    
    # Code index table
    c.execute('''
    CREATE TABLE IF NOT EXISTS code_index (
        id INTEGER PRIMARY KEY,
        file_path TEXT NOT NULL,
        content TEXT,
        language TEXT,
        last_modified DATETIME,
        size INTEGER
    )
    ''')
    
    # Project history table
    c.execute('''
    CREATE TABLE IF NOT EXISTS project_history (
        id INTEGER PRIMARY KEY,
        project_path TEXT NOT NULL,
        last_access DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()
    
    print(f"Database initialized at {DB_FILE}")

def log_command(command, output, working_dir, exit_code=0):
    """Log a command and its output to the database."""
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute(
        "INSERT INTO command_history (command, output, working_dir, exit_code) VALUES (?, ?, ?, ?)",
        (command, output, working_dir, exit_code)
    )
    
    conn.commit()
    conn.close()
    
    return True

def get_similar_commands(query, limit=5):
    """Get commands similar to the given query."""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Using LIKE for simple pattern matching
    c.execute(
        "SELECT command, output FROM command_history WHERE command LIKE ? ORDER BY timestamp DESC LIMIT ?",
        (f'%{query}%', limit)
    )
    
    rows = c.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def add_code_file(file_path, content, language):
    """Add or update a code file in the index."""
    file_stats = os.stat(file_path)
    
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute(
        """
        INSERT OR REPLACE INTO code_index 
        (file_path, content, language, last_modified, size) 
        VALUES (?, ?, ?, ?, ?)
        """,
        (file_path, content, language, file_stats.st_mtime, file_stats.st_size)
    )
    
    conn.commit()
    conn.close()
    
    return True

def search_code(query, limit=10):
    """Search the code index for the given query."""
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute(
        """
        SELECT file_path, content, language 
        FROM code_index 
        WHERE content LIKE ? 
        LIMIT ?
        """,
        (f'%{query}%', limit)
    )
    
    rows = c.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def update_project_history(project_path):
    """Update the last access time for a project."""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Check if project exists
    c.execute("SELECT id FROM project_history WHERE project_path = ?", (project_path,))
    project = c.fetchone()
    
    if project:
        # Update existing project
        c.execute(
            "UPDATE project_history SET last_access = CURRENT_TIMESTAMP WHERE id = ?",
            (project['id'],)
        )
    else:
        # Add new project
        c.execute(
            "INSERT INTO project_history (project_path) VALUES (?)",
            (project_path,)
        )
    
    conn.commit()
    conn.close()
    
    return True

def get_recent_projects(limit=5):
    """Get the most recently accessed projects."""
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute(
        "SELECT project_path, last_access FROM project_history ORDER BY last_access DESC LIMIT ?",
        (limit,)
    )
    
    rows = c.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]