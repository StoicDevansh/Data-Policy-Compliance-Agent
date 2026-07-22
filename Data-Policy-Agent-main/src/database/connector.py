"""
Database Connector - Multi-database connection manager supporting PostgreSQL, MySQL, SQLite, MongoDB.
"""
import asyncio
from typing import Dict, Any, List, Optional, Union
from abc import ABC, abstractmethod
from loguru import logger

try:
    from sqlalchemy import create_engine, text, inspect, MetaData
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

try:
    from pymongo import MongoClient
    from motor.motor_asyncio import AsyncIOMotorClient
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False


class BaseConnector(ABC):
    """Abstract base class for database connectors."""
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish database connection."""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close database connection."""
        pass
    
    @abstractmethod
    async def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """Execute a query and return results."""
        pass
    
    @abstractmethod
    async def get_tables(self) -> List[str]:
        """Get list of tables/collections in the database."""
        pass
    
    @abstractmethod
    async def get_schema(self, table: str) -> Dict[str, Any]:
        """Get schema information for a table."""
        pass
    
    @abstractmethod
    async def sample_data(self, table: str, limit: int = 100) -> List[Dict]:
        """Get sample data from a table."""
        pass


class SQLConnector(BaseConnector):
    """Connector for SQL databases (PostgreSQL, MySQL, SQLite)."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize SQL connector.
        
        Args:
            config: Database configuration with type, host, port, name, user, password
        """
        self.config = config
        self.db_type = config.get('type', 'sqlite').lower()
        self.engine = None
        self.connection = None
        self._build_connection_string()
    
    def _build_connection_string(self):
        """Build SQLAlchemy connection string based on config."""
        db_type = self.db_type
        
        if db_type == 'sqlite':
            db_name = self.config.get('name', self.config.get('database', 'database.db'))
            self.connection_string = f"sqlite:///{db_name}"
            self.async_connection_string = f"sqlite+aiosqlite:///{db_name}"
        
        elif db_type == 'postgresql':
            host = self.config.get('host', 'localhost')
            port = self.config.get('port', 5432)
            name = self.config.get('name', self.config.get('database', 'postgres'))
            user = self.config.get('user', 'postgres')
            password = self.config.get('password', '')
            
            self.connection_string = f"postgresql://{user}:{password}@{host}:{port}/{name}"
            self.async_connection_string = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"
        
        elif db_type in ('mysql', 'mariadb'):
            host = self.config.get('host', 'localhost')
            port = self.config.get('port', 3306)
            name = self.config.get('name', self.config.get('database', 'mysql'))
            user = self.config.get('user', 'root')
            password = self.config.get('password', '')
            
            self.connection_string = f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}"
            self.async_connection_string = f"mysql+aiomysql://{user}:{password}@{host}:{port}/{name}"
        
        else:
            # Use connection string directly if provided
            self.connection_string = self.config.get('connection_string', '')
            self.async_connection_string = self.connection_string
    
    async def connect(self) -> bool:
        """Establish database connection."""
        if not SQLALCHEMY_AVAILABLE:
            logger.error("SQLAlchemy not available. Install with: pip install sqlalchemy")
            return False
        
        try:
            # Create sync engine for schema inspection
            self.engine = create_engine(self.connection_string)
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info(f"Connected to {self.db_type} database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
    
    async def close(self) -> None:
        """Close database connection."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection closed")
    
    async def execute_query(
        self,
        query: str,
        params: Optional[Dict] = None
    ) -> List[Dict]:
        """Execute a query and return results."""
        if not self.engine:
            raise RuntimeError("Database not connected")
        
        def _execute():
            with self.engine.connect() as conn:
                result = conn.execute(text(query), params or {})
                
                # For SELECT queries, return results
                if result.returns_rows:
                    columns = result.keys()
                    return [dict(zip(columns, row)) for row in result.fetchall()]
                
                return []
        
        return await asyncio.get_event_loop().run_in_executor(None, _execute)
    
    async def get_tables(self) -> List[str]:
        """Get list of tables in the database."""
        if not self.engine:
            raise RuntimeError("Database not connected")
        
        def _get_tables():
            inspector = inspect(self.engine)
            return inspector.get_table_names()
        
        return await asyncio.get_event_loop().run_in_executor(None, _get_tables)
    
    async def get_schema(self, table: str) -> Dict[str, Any]:
        """Get schema information for a table."""
        if not self.engine:
            raise RuntimeError("Database not connected")
        
        def _get_schema():
            inspector = inspect(self.engine)
            
            columns = inspector.get_columns(table)
            pk_constraint = inspector.get_pk_constraint(table)
            foreign_keys = inspector.get_foreign_keys(table)
            indexes = inspector.get_indexes(table)
            
            return {
                "table_name": table,
                "columns": [
                    {
                        "name": col['name'],
                        "type": str(col['type']),
                        "nullable": col.get('nullable', True),
                        "default": str(col.get('default', ''))
                    }
                    for col in columns
                ],
                "primary_key": pk_constraint.get('constrained_columns', []),
                "foreign_keys": [
                    {
                        "columns": fk['constrained_columns'],
                        "referred_table": fk['referred_table'],
                        "referred_columns": fk['referred_columns']
                    }
                    for fk in foreign_keys
                ],
                "indexes": [
                    {
                        "name": idx['name'],
                        "columns": idx['column_names'],
                        "unique": idx.get('unique', False)
                    }
                    for idx in indexes
                ]
            }
        
        return await asyncio.get_event_loop().run_in_executor(None, _get_schema)
    
    async def sample_data(self, table: str, limit: int = 100) -> List[Dict]:
        """Get sample data from a table."""
        # Escape table name (basic protection)
        safe_table = table.replace('"', '').replace("'", '').replace(';', '')
        query = f'SELECT * FROM "{safe_table}" LIMIT {limit}'
        return await self.execute_query(query)
    
    async def get_row_count(self, table: str) -> int:
        """Get total row count for a table."""
        safe_table = table.replace('"', '').replace("'", '').replace(';', '')
        query = f'SELECT COUNT(*) as count FROM "{safe_table}"'
        result = await self.execute_query(query)
        return result[0]['count'] if result else 0
    
    async def get_distinct_values(
        self,
        table: str,
        column: str,
        limit: int = 100
    ) -> List[Any]:
        """Get distinct values for a column."""
        safe_table = table.replace('"', '').replace("'", '').replace(';', '')
        safe_column = column.replace('"', '').replace("'", '').replace(';', '')
        query = f'SELECT DISTINCT "{safe_column}" FROM "{safe_table}" LIMIT {limit}'
        result = await self.execute_query(query)
        return [row[column] for row in result]


class MongoConnector(BaseConnector):
    """Connector for MongoDB databases."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize MongoDB connector.
        
        Args:
            config: Database configuration with host, port, name, user, password
        """
        self.config = config
        self.client = None
        self.db = None
    
    async def connect(self) -> bool:
        """Establish MongoDB connection."""
        if not MONGODB_AVAILABLE:
            logger.error("pymongo/motor not available. Install with: pip install pymongo motor")
            return False
        
        try:
            host = self.config.get('host', 'localhost')
            port = self.config.get('port', 27017)
            name = self.config.get('name', self.config.get('database', 'test'))
            user = self.config.get('user')
            password = self.config.get('password')
            
            if user and password:
                connection_string = f"mongodb://{user}:{password}@{host}:{port}"
            else:
                connection_string = f"mongodb://{host}:{port}"
            
            self.client = AsyncIOMotorClient(connection_string)
            self.db = self.client[name]
            
            # Test connection
            await self.client.admin.command('ping')
            
            logger.info(f"Connected to MongoDB database: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False
    
    async def close(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    async def execute_query(
        self,
        query: str,
        params: Optional[Dict] = None
    ) -> List[Dict]:
        """Execute a MongoDB query (using aggregation pipeline)."""
        # For MongoDB, expect query to be collection name
        # and params to contain the pipeline or filter
        if not self.db:
            raise RuntimeError("Database not connected")
        
        collection_name = query
        collection = self.db[collection_name]
        
        if params and 'pipeline' in params:
            cursor = collection.aggregate(params['pipeline'])
        elif params and 'filter' in params:
            cursor = collection.find(params['filter'])
        else:
            cursor = collection.find({})
        
        results = []
        async for doc in cursor:
            doc['_id'] = str(doc['_id'])  # Convert ObjectId to string
            results.append(doc)
        
        return results
    
    async def get_tables(self) -> List[str]:
        """Get list of collections in the database."""
        if not self.db:
            raise RuntimeError("Database not connected")
        
        return await self.db.list_collection_names()
    
    async def get_schema(self, table: str) -> Dict[str, Any]:
        """Infer schema from MongoDB collection sample."""
        if not self.db:
            raise RuntimeError("Database not connected")
        
        collection = self.db[table]
        
        # Sample documents to infer schema
        sample = await collection.find_one()
        
        if not sample:
            return {"collection_name": table, "fields": []}
        
        def infer_type(value):
            if value is None:
                return "null"
            return type(value).__name__
        
        fields = [
            {"name": key, "type": infer_type(value)}
            for key, value in sample.items()
        ]
        
        return {
            "collection_name": table,
            "fields": fields,
            "sample_document": {k: str(v) for k, v in sample.items()}
        }
    
    async def sample_data(self, table: str, limit: int = 100) -> List[Dict]:
        """Get sample data from a collection."""
        if not self.db:
            raise RuntimeError("Database not connected")
        
        collection = self.db[table]
        cursor = collection.find({}).limit(limit)
        
        results = []
        async for doc in cursor:
            doc['_id'] = str(doc['_id'])
            results.append(doc)
        
        return results


class DatabaseConnector:
    """
    Factory class for creating appropriate database connectors.
    Provides unified interface for different database types.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize database connector.
        
        Args:
            config: Database configuration including 'type' field
        """
        self.config = config
        self.db_type = config.get('type', 'sqlite').lower()
        
        # Create appropriate connector
        if self.db_type == 'mongodb':
            self._connector = MongoConnector(config)
        else:
            self._connector = SQLConnector(config)
    
    async def connect(self) -> bool:
        """Establish database connection."""
        return await self._connector.connect()
    
    async def close(self) -> None:
        """Close database connection."""
        await self._connector.close()
    
    async def execute_query(
        self,
        query: str,
        params: Optional[Dict] = None
    ) -> List[Dict]:
        """Execute a query and return results."""
        return await self._connector.execute_query(query, params)
    
    async def get_tables(self) -> List[str]:
        """Get list of tables/collections."""
        return await self._connector.get_tables()
    
    async def get_schema(self, table: str) -> Dict[str, Any]:
        """Get schema information for a table/collection."""
        return await self._connector.get_schema(table)
    
    async def sample_data(self, table: str, limit: int = 100) -> List[Dict]:
        """Get sample data from a table/collection."""
        return await self._connector.sample_data(table, limit)
    
    async def get_full_schema(self) -> Dict[str, Any]:
        """Get schema for all tables/collections."""
        tables = await self.get_tables()
        schemas = {}
        
        for table in tables:
            try:
                schemas[table] = await self.get_schema(table)
            except Exception as e:
                logger.warning(f"Failed to get schema for {table}: {e}")
                schemas[table] = {"error": str(e)}
        
        return schemas
    
    @property
    def is_sql(self) -> bool:
        """Check if this is a SQL database."""
        return self.db_type != 'mongodb'
    
    @property
    def connector(self) -> BaseConnector:
        """Get the underlying connector."""
        return self._connector
