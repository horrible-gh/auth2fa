"""Storage modules for auth2fa."""
from .base import BaseStorage
from .json_storage import JSONStorage
from .sql_storage import SQLStorage

__all__ = ['BaseStorage', 'JSONStorage', 'SQLStorage']