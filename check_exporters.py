from models import SchemaResponse, TableInfo, ColumnInfo, ForeignKeyInfo
from exporters import export_sql, export_dbml, export_markdown, export_json

schema = SchemaResponse(
    database="demo",
    tables=[
        TableInfo(
            name="users",
            columns=[
                ColumnInfo(name="id", data_type="bigint", is_pk=True, is_nullable=False),
                ColumnInfo(name="name", data_type="varchar", is_nullable=True),
            ],
        ),
        TableInfo(
            name="orders",
            columns=[
                ColumnInfo(name="id", data_type="bigint", is_pk=True, is_nullable=False),
                ColumnInfo(name="user_id", data_type="bigint", is_nullable=False),
            ],
            foreign_keys=[
                ForeignKeyInfo(constrained_column="user_id", referred_table="users", referred_column="id")
            ],
        ),
    ],
)

sql = export_sql(schema)
dbml = export_dbml(schema)
md = export_markdown(schema)
js = export_json(schema)

assert "CREATE TABLE `users`" in sql
assert "FOREIGN KEY (`user_id`)" in sql
assert "Table users {" in dbml
assert "Ref: orders.user_id > users.id" in dbml
assert "### Table: `orders`" in md
assert '"database": "demo"' in js
print("exporters OK")
