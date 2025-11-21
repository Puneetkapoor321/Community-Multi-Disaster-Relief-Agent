import os
import json
from datetime import datetime
import sqlite3


DB_PATH = os.getenv('MEMORY_DB', 'memory.db')
_conn = None


def get_conn():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
    return _conn


def now_iso():


    return datetime.utcnow().isoformat() + 'Z'


def save_json_field(obj):


    return json.dumps(obj)
