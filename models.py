"""
Unified models for Schema Visualizer.
"""
from typing import List, Optional, Any, Dict
from pydantic import BaseModel

class ColumnInfo(BaseModel):
    name: str
    data_type: str
    is_pk: bool = False
    is_nullable: bool = True
    default: Optional[str] = None
    extra: Optional[str] = None

class ForeignKeyInfo(BaseModel):
    constrained_column: str
    referred_table: str
    referred_column: str
    name: Optional[str] = None

class IndexInfo(BaseModel):
    name: str
    columns: List[str]
    is_unique: bool = False

class TableInfo(BaseModel):
    name: str
    table_type: str = "table" # table, collection, view
    columns: List[ColumnInfo] = []
    foreign_keys: List[ForeignKeyInfo] = []
    indexes: List[IndexInfo] = []
    metadata: Dict[str, Any] = {}

class SchemaResponse(BaseModel):
    database: str
    tables: List[TableInfo] = []
    inferred_relations: List[Dict[str, Any]] = []

class ConnectionConfig(BaseModel):
    id: Optional[str] = None
    name: str
    db_type: str # postgres, mysql, mariadb, mongodb, redis, sqlite
    host: Optional[str] = "localhost"
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None
    options: Dict[str, Any] = {}
