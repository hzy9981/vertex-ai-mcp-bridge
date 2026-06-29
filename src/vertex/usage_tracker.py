import os
import json
import sqlite3
import datetime
import tiktoken
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "usage.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS token_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            tool_name TEXT,
            model_name TEXT,
            input_tokens INTEGER,
            output_tokens INTEGER,
            total_tokens INTEGER,
            metadata TEXT
        )
    """)
    conn.commit()
    conn.close()

def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

def log_usage(tool_name: str, model_name: str, input_text: str, output_text: str, metadata: Optional[dict] = None):
    input_tokens = count_tokens(input_text, model_name)
    output_tokens = count_tokens(output_text, model_name)
    total_tokens = input_tokens + output_tokens
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO token_usage (tool_name, model_name, input_tokens, output_tokens, total_tokens, metadata)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (tool_name, model_name, input_tokens, output_tokens, total_tokens, json.dumps(metadata)))
    conn.commit()
    conn.close()
    print(f"[Usage Stats] Tool: {tool_name}, Tokens: {total_tokens} ({input_tokens} in / {output_tokens} out)")

def get_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(total_tokens), SUM(input_tokens), SUM(output_tokens), COUNT(*) FROM token_usage")
    stats = cursor.fetchone()
    conn.close()
    return {
        "total_tokens": stats[0] or 0,
        "input_tokens": stats[1] or 0,
        "output_tokens": stats[2] or 0,
        "request_count": stats[3] or 0
    }

init_db()
