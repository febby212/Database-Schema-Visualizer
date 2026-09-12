from abc import ABC, abstractmethod
from typing import List, Dict, Any
from models import TableInfo, SchemaResponse, ConnectionConfig

class BaseAdapter(ABC):
    def __init__(self, config: ConnectionConfig):
        self.config = config

    @abstractmethod
    def test_connection(self) -> bool:
        """Test if the connection credentials work."""
        pass

    @abstractmethod
    def get_databases(self) -> List[str]:
        """List databases/schemas accessible."""
        pass

    @abstractmethod
    def get_schema(self, database_name: str) -> SchemaResponse:
        """Get full schema (tables, columns, relations) for a database."""
        pass
