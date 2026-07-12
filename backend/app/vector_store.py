from __future__ import annotations

import json
import math
import os
import sqlite3
from dataclasses import dataclass
from typing import Dict, List, Optional

from .embedding import embed_texts
from .config import settings


def _storage_dir() -> str:
    base = os.path.join(os.path.dirname(__file__), '..', 'storage')
    os.makedirs(base, exist_ok=True)
    return os.path.abspath(base)


def _db_path() -> str:
    return os.path.join(_storage_dir(), 'vector_store.sqlite3')


def _connect():
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS vectors (
            collection TEXT NOT NULL,
            item_id INTEGER NOT NULL,
            doc_id INTEGER,
            chunk_index INTEGER,
            text TEXT,
            vector_json TEXT NOT NULL,
            payload_json TEXT,
            PRIMARY KEY(collection, item_id)
        )
        '''
    )
    conn.commit()
    return conn


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


@dataclass
class LocalHit:
    id: int
    score: float
    payload: Dict


class LocalQdrantClient:
    def recreate_collection(self, collection_name: str, vectors_count: int = 0, vector_size: int = 0):
        # Collections are implicit in SQLite; method kept for API compatibility.
        return None

    def upsert(self, collection_name: str, points: List[Dict]):
        conn = _connect()
        for point in points:
            payload = point.get('payload') or {}
            conn.execute(
                '''
                INSERT OR REPLACE INTO vectors
                (collection, item_id, doc_id, chunk_index, text, vector_json, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    collection_name,
                    int(point['id']),
                    payload.get('doc_id'),
                    payload.get('chunk_index'),
                    payload.get('text'),
                    json.dumps(point['vector']),
                    json.dumps(payload),
                ),
            )
        conn.commit()
        conn.close()

    def search(self, collection_name: str, query_vector: List[float], limit: int = 5):
        conn = _connect()
        rows = conn.execute(
            'SELECT item_id, payload_json, vector_json FROM vectors WHERE collection = ?',
            (collection_name,),
        ).fetchall()
        conn.close()
        hits: List[LocalHit] = []
        for row in rows:
            payload = json.loads(row['payload_json']) if row['payload_json'] else {}
            vector = json.loads(row['vector_json'])
            score = _cosine_similarity(query_vector, vector)
            hits.append(LocalHit(id=int(row['item_id']), score=score, payload=payload))
        hits.sort(key=lambda item: item.score, reverse=True)
        return hits[:limit]


def get_qdrant_client():
    # Use local storage by default so the project runs without external Qdrant.
    return LocalQdrantClient()
