from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn

from models import ConnectionConfig, SchemaResponse
from db.postgres import PostgresAdapter
from db.mysql import MySQLAdapter
from db.mongodb import MongoDBAdapter
from db.redis import RedisAdapter
from exporters import export_sql, export_dbml, export_markdown, export_json
from connections import save_connection, get_all_connections, get_connection, delete_connection

app = FastAPI(title="DB Schema Visualizer")
app.mount("/static", StaticFiles(directory="static"), name="static")

ADAPTERS = {
    "postgres": PostgresAdapter,
    "postgresql": PostgresAdapter,
    "mysql": MySQLAdapter,
    "mariadb": MySQLAdapter,
    "mongodb": MongoDBAdapter,
    "redis": RedisAdapter,
}

class ConnectRequest(BaseModel):
    id: Optional[str] = None
    type: str
    host: Optional[str] = None
    port: Optional[int] = None
    user: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None
    name: Optional[str] = None
    options: Dict[str, Any] = {}

class ListDbsRequest(BaseModel):
    connection_id: str

class SchemaRequest(BaseModel):
    connection_id: str
    database: str

class ExportRequest(BaseModel):
    connection_id: str
    database: str
    format: str  # sql, dbml, markdown, json

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/api/health")
async def health():
    return {"status": "ok"}

@app.post("/api/connect")
async def connect(req: ConnectRequest):
    adapter_cls = ADAPTERS.get(req.type.lower())
    if not adapter_cls:
        raise HTTPException(status_code=400, detail=f"Unsupported DB type: {req.type}")
    try:
        config = ConnectionConfig(
            id=req.id,
            name=req.name or f"{req.type}_{req.host or 'localhost'}_{req.port or ''}",
            db_type=req.type.lower(),
            host=req.host,
            port=req.port,
            username=req.user,
            password=req.password,
            database=req.database,
            options=req.options,
        )
        adapter = adapter_cls(config)
        adapter.test_connection()
        conn_id = save_connection(config)
        return {"success": True, "connection_id": conn_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/connections")
async def list_connections():
    conns = get_all_connections()
    return [c.model_dump() for c in conns]

@app.post("/api/list-databases")
async def list_databases(req: ListDbsRequest):
    conn = get_connection(req.connection_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    adapter_cls = ADAPTERS.get(conn.db_type)
    adapter = adapter_cls(conn)
    try:
        dbs = adapter.get_databases()
        return {"databases": dbs}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/schema")
async def get_schema(req: SchemaRequest):
    conn = get_connection(req.connection_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    adapter_cls = ADAPTERS.get(conn.db_type)
    adapter = adapter_cls(conn)
    try:
        schema = adapter.get_schema(req.database)
        return schema.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/export")
async def export_schema(req: ExportRequest):
    conn = get_connection(req.connection_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    adapter_cls = ADAPTERS.get(conn.db_type)
    adapter = adapter_cls(conn)
    try:
        schema = adapter.get_schema(req.database)
        fmt = req.format.lower()
        if fmt == "sql":
            content = export_sql(schema)
            media_type = "text/plain"
        elif fmt == "dbml":
            content = export_dbml(schema)
            media_type = "text/plain"
        elif fmt == "markdown":
            content = export_markdown(schema)
            media_type = "text/markdown"
        elif fmt == "json":
            content = export_json(schema)
            media_type = "application/json"
        else:
            raise HTTPException(status_code=400, detail="Unsupported format")
        return PlainTextResponse(content, media_type=media_type)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/connections/{conn_id}")
async def delete_conn(conn_id: str):
    delete_connection(conn_id)
    return {"success": True}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=False)