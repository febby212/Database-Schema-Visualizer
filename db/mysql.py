import mysql.connector
from typing import List
from models import SchemaResponse, TableInfo, ColumnInfo, ForeignKeyInfo, ConnectionConfig
from db.base import BaseAdapter

class MySQLAdapter(BaseAdapter):
    def _get_connection(self, database: str = None):
        return mysql.connector.connect(
            host=self.config.host or "localhost",
            port=self.config.port or 3306,
            user=self.config.username or "root",
            password=self.config.password or "",
            database=database or self.config.database,
            connection_timeout=5
        )

    def test_connection(self) -> bool:
        try:
            conn = self._get_connection()
            conn.close()
            return True
        except Exception as e:
            raise RuntimeError(f"MySQL connection failed: {str(e)}")

    def get_databases(self) -> List[str]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SHOW DATABASES;")
        dbs = [row[0] for row in cursor.fetchall() if row[0] not in ('information_schema', 'mysql', 'performance_schema', 'sys')]
        conn.close()
        return dbs

    def get_schema(self, database_name: str) -> SchemaResponse:
        conn = self._get_connection(database_name)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT TABLE_NAME, TABLE_TYPE FROM information_schema.TABLES WHERE TABLE_SCHEMA = %s", (database_name,))
        tables_data = cursor.fetchall()

        tables: List[TableInfo] = []

        for t in tables_data:
            tname = t["TABLE_NAME"]

            # Columns
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_KEY
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                ORDER BY ORDINAL_POSITION
            """, (database_name, tname))
            
            columns = []
            for col in cursor.fetchall():
                columns.append(ColumnInfo(
                    name=col["COLUMN_NAME"],
                    data_type=col["DATA_TYPE"],
                    is_pk=(col["COLUMN_KEY"] == "PRI"),
                    is_nullable=(col["IS_NULLABLE"] == "YES"),
                    default=col["COLUMN_DEFAULT"]
                ))

            # Foreign Keys
            cursor.execute("""
                SELECT 
                    COLUMN_NAME, 
                    REFERENCED_TABLE_NAME, 
                    REFERENCED_COLUMN_NAME,
                    CONSTRAINT_NAME
                FROM information_schema.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = %s 
                  AND TABLE_NAME = %s 
                  AND REFERENCED_TABLE_NAME IS NOT NULL
            """, (database_name, tname))

            fks = []
            for fk in cursor.fetchall():
                fks.append(ForeignKeyInfo(
                    constrained_column=fk["COLUMN_NAME"],
                    referred_table=fk["REFERENCED_TABLE_NAME"],
                    referred_column=fk["REFERENCED_COLUMN_NAME"],
                    name=fk["CONSTRAINT_NAME"]
                ))

            tables.append(TableInfo(
                name=tname,
                table_type="table",
                columns=columns,
                foreign_keys=fks
            ))

        conn.close()
        return SchemaResponse(database=database_name, tables=tables)
