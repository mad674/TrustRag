import sqlite3
import json
import hashlib
from typing import List, Optional

DB_PATH = None

def init(db_path: str):
    global DB_PATH
    DB_PATH = db_path
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS embeddings_cache (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    conn.commit()
    conn.close()


def _make_key(texts: List[str]) -> str:
    h = hashlib.sha256('\n'.join(texts).encode('utf-8')).hexdigest()
    return h


def get(texts: List[str]) -> Optional[List[List[float]]]:
    if DB_PATH is None:
        return None
    key = _make_key(texts)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT value FROM embeddings_cache WHERE key=?', (key,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return json.loads(row[0])


def set_(texts: List[str], vectors: List[List[float]]):
    if DB_PATH is None:
        return
    key = _make_key(texts)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('REPLACE INTO embeddings_cache (key,value) VALUES (?,?)', (key, json.dumps(vectors)))
    conn.commit()
    conn.close()
