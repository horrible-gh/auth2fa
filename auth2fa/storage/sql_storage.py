"""SQL database storage implementation using sqloader."""
import json
from typing import Optional
from .base import BaseStorage


class SQLStorage(BaseStorage):
    """SQL database storage implementation using sqloader."""

    def __init__(self, sq, table_prefix: str = "totp_auth"):
        """
        Initialize SQL storage.

        Args:
            sq: sqloader instance (SQLite3 or MySQL)
            table_prefix: SQL file directory name (default: totp_auth)
        """
        self.db = sq
        self.table_prefix = table_prefix
        self._ensure_table_exists()

    def _ensure_table_exists(self) -> None:
        """Create the TOTP table if it doesn't exist."""
        # sqloader will execute the create_table.sql file
        self.db.execute(f"{self.table_prefix}/create_table")

    def save(self, user_id: str, data: dict) -> None:
        """
        Save or update TOTP data for a user.

        Args:
            user_id: Unique identifier for the user (converted to str)
            data: Dictionary containing TOTP data
        """
        user_id = str(user_id)  # Ensure user_id is string

        # Use INSERT with ON CONFLICT (UPSERT)
        self.db.execute(
            f"{self.table_prefix}/insert",
            user_id=user_id,
            secret=data.get('secret'),
            enabled=data.get('enabled', False),
            recovery_codes=json.dumps(data.get('recovery_codes', [])),
            created_at=data.get('created_at')
        )

    def get(self, user_id: str) -> Optional[dict]:
        """
        Retrieve TOTP data for a user.

        Args:
            user_id: Unique identifier for the user (converted to str)

        Returns:
            Dictionary containing TOTP data, or None if not found
        """
        user_id = str(user_id)  # Ensure user_id is string

        result = self.db.execute(
            f"{self.table_prefix}/select_by_user",
            user_id=user_id
        )

        if not result:
            return None

        row = result[0]
        return {
            'secret': row.get('secret'),
            'enabled': bool(row.get('enabled')),
            'recovery_codes': json.loads(row.get('recovery_codes', '[]')),
            'created_at': row.get('created_at')
        }

    def delete(self, user_id: str) -> None:
        """
        Delete TOTP data for a user.

        Args:
            user_id: Unique identifier for the user (converted to str)
        """
        user_id = str(user_id)  # Ensure user_id is string

        self.db.execute(
            f"{self.table_prefix}/delete",
            user_id=user_id
        )

    def exists(self, user_id: str) -> bool:
        """
        Check if TOTP is configured for a user.

        Args:
            user_id: Unique identifier for the user (converted to str)

        Returns:
            True if TOTP data exists, False otherwise
        """
        user_id = str(user_id)  # Ensure user_id is string

        result = self.db.execute(
            f"{self.table_prefix}/select_by_user",
            user_id=user_id
        )
        return len(result) > 0
