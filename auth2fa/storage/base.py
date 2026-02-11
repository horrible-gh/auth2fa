"""Base storage interface for auth2fa."""
from abc import ABC, abstractmethod
from typing import Optional


class BaseStorage(ABC):
    """Abstract base class for TOTP storage implementations."""

    @abstractmethod
    def save(self, user_id: str, data: dict) -> None:
        """
        Save or update TOTP data for a user.

        Args:
            user_id: Unique identifier for the user
            data: Dictionary containing TOTP data with structure:
                {
                    "secret": "BASE32SECRET",
                    "enabled": False,
                    "recovery_codes": ["A3F8K2M1", "B7D2N4P9", ...],
                    "created_at": "2026-02-11T18:00:00"
                }
        """
        pass

    @abstractmethod
    def get(self, user_id: str) -> Optional[dict]:
        """
        Retrieve TOTP data for a user.

        Args:
            user_id: Unique identifier for the user

        Returns:
            Dictionary containing TOTP data, or None if not found
        """
        pass

    @abstractmethod
    def delete(self, user_id: str) -> None:
        """
        Delete TOTP data for a user.

        Args:
            user_id: Unique identifier for the user
        """
        pass

    @abstractmethod
    def exists(self, user_id: str) -> bool:
        """
        Check if TOTP is configured for a user.

        Args:
            user_id: Unique identifier for the user

        Returns:
            True if TOTP data exists, False otherwise
        """
        pass