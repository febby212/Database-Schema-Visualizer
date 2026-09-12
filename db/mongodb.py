import json
from typing import List, Dict, Any
from models import SchemaResponse, TableInfo, ColumnInfo, ForeignKeyInfo, ConnectionConfig
from db.base import BaseAdapter

class MongoDBAdapter(BaseAdapter):
    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        from pymongo import MongoClient
        self.client = MongoClient(
            host=self.config.host or "localhost",
            port=self.config.port or 27017,
            username=self.config.username,
            password=self.config.password,
            authSource=self.config.database or "admin",
            serverSelectionTimeoutMS=5000
        )

    def test_connection(self) -> bool:
        try:
            # ping works for both standalone and replica set
            self.client.admin.command('ping')
            return True
        except Exception as e:
            raise RuntimeError(f"MongoDB connection failed: {str(e)}")

    def get_databases(self) -> List[str]:
        # Exclude admin and local DBs that hold system metadata
        dbs = [db for db in self.client.list_database_names() if db not in ("admin", "local", "config")]
        return dbs

    def get_schema(self, database_name: str) -> SchemaResponse:
        db = self.client[database_name]
        collections = db.list_collection_names()
        tables: List[TableInfo] = []
        inferred: List[Dict[str, Any]] = []
        for coll in collections:
            # Sample 100 docs to infer fields
            sample = list(db[coll].find().limit(100))
            # Simple field inference: collect names and types for top-level fields.
            field_stats: Dict[str, set] = {}
            for doc in sample:
                for k, v in doc.items():
                    field_stats.setdefault(k, set()).add(type(v).__name__)
            columns = []
            for fname, types in field_stats.items():
                dtype = ",".join(sorted(types))
                columns.append(ColumnInfo(name=fname, data_type=dtype, is_pk=False, is_nullable=True))
            tables.append(TableInfo(name=coll, table_type="collection", columns=columns, foreign_keys=[]))
            # Infer relationships: look for fields ending with _id that match other collection names
            for fname in field_stats:
                if fname.lower().endswith('_id'):
                    target = fname[:-3]
                    if target in collections:
                        inferred.append({
                            "from_table": coll,
                            "from_field": fname,
                            "to_table": target,
                            "to_field": "_id",
                            "confidence": 0.9
                        })
        return SchemaResponse(database=database_name, tables=tables, inferred_relations=inferred)
