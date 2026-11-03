"""
Database module for Food Waste Management Dashboard.
Provides safe database connections, query execution, and predefined queries.
"""
from .connection import get_db_connection, run_query, test_connection, get_db_config
from .queries import PREDEFINED_QUERIES, SAFE_READONLY_PATTERN

__all__ = [
    "get_db_connection",
    "run_query",
    "test_connection",
    "get_db_config",
    "PREDEFINED_QUERIES",
    "SAFE_READONLY_PATTERN",
]
