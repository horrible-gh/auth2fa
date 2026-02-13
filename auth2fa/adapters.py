"""Database adapters for auth2fa.

This module provides adapters to connect auth2fa with different database libraries.
Adapters are optional and only loaded when the corresponding library is available.
"""
import os
import re


class Auth2FAAdapter:
    """
    Adapter that bridges auth2fa's SQLStorage with sqloader's database instances.

    This adapter provides the execute(path, **kwargs) interface expected by SQLStorage
    and translates it to sqloader's native database operations.

    Features:
    - Automatic SQL file loading from auth2fa/sql directory
    - Parameter binding conversion (SQLite vs MySQL)
    - SQL dialect conversion (ON CONFLICT vs ON DUPLICATE KEY UPDATE)
    - Support for both SELECT and DML statements

    Example:
        >>> from sqloader import SQLiteWrapper
        >>> from auth2fa.adapters import Auth2FAAdapter
        >>>
        >>> db = SQLiteWrapper('database.db')
        >>> adapter = Auth2FAAdapter(db)
        >>> storage = SQLStorage(adapter)
    """

    def __init__(self, db_instance):
        """
        Initialize the adapter.

        Args:
            db_instance: sqloader database instance (SQLiteWrapper or MySQLWrapper)
        """
        self.db = db_instance
        import auth2fa as _auth2fa_mod
        self._sql_dir = os.path.join(os.path.dirname(_auth2fa_mod.__file__), "sql")

    def _is_mysql(self):
        """Check if the database is MySQL/MariaDB."""
        try:
            from sqloader._prototype import MYSQL
            return getattr(self.db, "db_type", None) == MYSQL
        except ImportError:
            # If sqloader._prototype is not available, check alternative methods
            return False

    def _prepare(self, sql, kwargs):
        """
        Prepare SQL and parameters for the target database.

        Conversions:
        - SQLite: :param_name format, params as dict
        - MySQL: %s format (positional), params as list
                 ON CONFLICT → ON DUPLICATE KEY UPDATE

        Args:
            sql: SQL query string
            kwargs: Named parameters

        Returns:
            tuple: (converted_sql, converted_params)
        """
        if not kwargs:
            params = None
        elif self._is_mysql():
            # Extract parameter names in order and convert :param_name → %s
            param_names = re.findall(r":(\w+)", sql)
            sql = re.sub(r":\w+", "%s", sql)

            # Convert ON CONFLICT to ON DUPLICATE KEY UPDATE for MySQL
            def replace_conflict(m):
                set_clause = m.group(1)
                pairs = re.findall(r"(\w+)\s*=\s*EXCLUDED\.\w+", set_clause)
                updates = ", ".join(f"{col} = VALUES({col})" for col in pairs)
                return f"ON DUPLICATE KEY UPDATE {updates}"

            sql = re.sub(
                r"ON CONFLICT\s*\([^)]+\)\s*DO UPDATE\s+SET\s+((?:\w+\s*=\s*EXCLUDED\.\w+,?\s*)+)",
                replace_conflict,
                sql,
                flags=re.IGNORECASE,
            )
            params = [kwargs[name] for name in param_names]
        else:
            params = kwargs

        return sql, params

    def execute(self, path, **kwargs):
        """
        Execute SQL from file with parameter binding.

        This method provides the interface expected by auth2fa's SQLStorage.

        Args:
            path: SQL file path relative to auth2fa/sql directory (without .sql extension)
            **kwargs: Named parameters for SQL binding

        Returns:
            list: For SELECT queries, returns list of dicts. For DML, returns empty list.
        """
        sql_file = os.path.join(self._sql_dir, path + ".sql")
        with open(sql_file, "r", encoding="utf-8") as f:
            raw_sql = f.read()

        # Remove SQL comments
        lines = [l for l in raw_sql.splitlines() if not l.strip().startswith("--")]
        sql_stripped = " ".join(lines).strip()

        sql_stripped, params = self._prepare(sql_stripped, kwargs)

        # Execute based on query type
        if sql_stripped.upper().startswith("SELECT"):
            rows = self.db.fetch_all(sql_stripped, params)
            if rows is None:
                return []
            return [dict(row) for row in rows]
        else:
            # Handle multiple statements (e.g., CREATE TABLE + CREATE INDEX)
            statements = [s.strip() for s in sql_stripped.split(";") if s.strip()]
            for stmt in statements:
                self.db.execute(stmt, params)
            return []


# Export only if sqloader is available
__all__ = []

try:
    import sqloader  # noqa: F401
    __all__.append('Auth2FAAdapter')
except ImportError:
    pass
