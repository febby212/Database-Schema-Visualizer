import psycopg2
from typing import List
from models import SchemaResponse, TableInfo, ColumnInfo, ForeignKeyInfo, IndexInfo, ConnectionConfig
from db.base import BaseAdapter

class PostgresAdapter(BaseAdapter):
    def _get_connection(self, database: str = None):
        db_name = database or self.config.database or "postgres"
        return psycopg2.connect(
            host=self.config.host or "localhost",
            port=self.config.port or 5432,
            user=self.config.username or "postgres",
            password=self.config.password or "",
            dbname=db_name,
            connect_timeout=5
        )

    def test_connection(self) -> bool:
        try:
            conn = self._get_connection()
            conn.close()
            return True
        except Exception as e:
            raise RuntimeError(f"PostgreSQL connection failed: {str(e)}")

    def get_databases(self) -> List[str]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname;")
        dbs = [row[0] for row in cursor.fetchall()]
        conn.close()
        return dbs

    def get_schema(self, database_name: str) -> SchemaResponse:
        conn = self._get_connection(database_name)
        cursor = conn.cursor()

        # 1. Get Tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        table_names = [r[0] for r in cursor.fetchall()]

        tables: List[TableInfo] = []

        for tname in table_names:
            # Columns
            cursor.execute("""
                SELECT 
                    c.column_name, 
                    c.data_type, 
                    c.is_nullable, 
                    c.column_default,
                    CASE WHEN pk.column_name IS NOT NULL THEN true ELSE false END as is_pk
                FROM information_schema.columns c
                LEFT JOIN (
                    SELECT kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                        ON tc.constraint_name = kcu.constraint_name 
                        AND tc.table_schema = kcu.table_schema
                    WHERE tc.constraint_type = 'PRIMARY KEY' 
                        AND tc.table_name = %s
                ) pk ON c.column_name = pk.column_name
                WHERE c.table_schema = 'public' AND c.table_name = %s
                ORDER BY c.ordinal_position;
            """, (tname, tname))

            columns = []
            for col in cursor.fetchall():
                cname, dtype, nullable, default, is_pk = col
                columns.append(ColumnInfo(
                    name=cname,
                    data_type=dtype,
                    is_pk=bool(is_pk),
                    is_nullable=(nullable == 'YES'),
                    default=str(default) if default is not None else None
                ))

            # Foreign Keys
            cursor.execute("""
                SELECT
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name,
                    tc.constraint_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = %s;
            """, (tname,))

            fks = []
            for fk in cursor.fetchall():
                col_name, ftable, fcol, constraint_name = fk
                fks.append(ForeignKeyInfo(
                    constrained_column=col_name,
                    referred_table=ftable,
                    referred_column=fcol,
                    name=constraint_name
                ))

            tables.append(TableInfo(
                name=tname,
                table_type="table",
                columns=columns,
                foreign_keys=fks
            ))

        conn.close()
        return SchemaResponse(database=database_name, tables=tables)
