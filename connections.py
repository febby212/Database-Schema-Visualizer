import sqlite3
import json
from typing import List, Optional
from models import ConnectionConfig

from pathlib import Path

DB_PATH = str(Path(__file__).resolve().parent / "connections.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS connections (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            db_type TEXT NOT NULL,
            host TEXT,
            port INTEGER,
            username TEXT,
            password TEXT,
            database TEXT,
            options TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_connection(config: ConnectionConfig) -> str:
    init_db()
    import uuid
    conn_id = config.id or str(uuid.uuid4())
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO connections (id, name, db_type, host, port, username, password, database, options)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        conn_id,
        config.name,
        config.db_type,
        config.host,
        config.port,
        config.username,
        config.password,
        config.database,
        json.dumps(config.options)
    ))
    conn.commit()
    conn.close()
    return conn_id

def get_all_connections() -> List[ConnectionConfig]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM connections")
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for r in rows:
        result.append(ConnectionConfig(
            id=r["id"],
            name=r["name"],
            db_type=r["db_type"],
            host=r["host"],
            port=r["port"],
            username=r["username"],
            password=r["password"],
            database=r["database"],
            options=json.loads(r["options"] or "{}")
        ))
    return result

def get_connection(conn_id: str) -> Optional[ConnectionConfig]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM connections WHERE id = ?", (conn_id,))
    r = cursor.fetchone()
    conn.close()
    
    if not r:
        return None
    return ConnectionConfig(
        id=r["id"],
        name=r["name"],
        db_type=r["db_type"],
        host=r["host"],
        port=r["port"],
        username=r["username"],
        password=r["password"],
        database=r["database"],
        options=json.loads(r["options"] or "{}")
    )

def delete_connection(conn_id: str):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM connections WHERE id = ?", (conn_id,))
    conn.commit()
    conn.close()
