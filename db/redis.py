import redis
from typing import List
from models import SchemaResponse, TableInfo, ColumnInfo, ConnectionConfig
from db.base import BaseAdapter

class RedisAdapter(BaseAdapter):
    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        self.client = redis.Redis(
            host=self.config.host or "localhost",
            port=self.config.port or 6379,
            password=self.config.password,
            decode_responses=True
        )

    def test_connection(self) -> bool:
        try:
            self.client.ping()
            return True
        except Exception as e:
            raise RuntimeError(f"Redis connection failed: {str(e)}")

    def get_databases(self) -> List[str]:
        # Redis has a single logical DB index (0-15 by default). Return names like db0, db1, ...
        try:
            cfg = self.client.config_get('databases')
            num = int(cfg.get('databases', 16))
        except Exception:
            num = 16
        return [f"db{i}" for i in range(num)]

    def get_schema(self, database_name: str) -> SchemaResponse:
        # Switch to requested DB
        db_index = int(database_name.replace('db', ''))
        self.client.execute_command('SELECT', db_index)
        keys = self.client.keys('*')
        tables: List[TableInfo] = []
        for key in keys[:500]:  # limit to 500 keys
            ktype = self.client.type(key)
            columns = [
                ColumnInfo(name='key', data_type='text', is_pk=True, is_nullable=False),
                ColumnInfo(name='type', data_type=ktype, is_pk=False, is_nullable=False),
            ]
            tables.append(TableInfo(name=key, table_type='key', columns=columns, foreign_keys=[]))
        return SchemaResponse(database=database_name, tables=tables)
