"""JSON file-based storage implementation for auth2fa."""
import json
import time
from pathlib import Path
from typing import Optional
from .base import BaseStorage


class JSONStorage(BaseStorage):
    """JSON file-based storage implementation with file locking."""

    def __init__(self, storage_path: str = "./totp_data.json"):
        """
        Initialize JSON storage.

        Args:
            storage_path: Path to the JSON file for storing TOTP data
        """
        self.file_path = Path(storage_path)
        self.lock_path = Path(str(self.file_path) + ".lock")
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """Create the JSON file if it doesn't exist."""
        if not self.file_path.exists():
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            self._write_data({})

    def _acquire_lock(self, timeout: int = 5) -> None:
        """
        Acquire file lock using lock file.

        Args:
            timeout: Maximum time to wait for lock in seconds
        """
        start_time = time.time()
        while self.lock_path.exists():
            if time.time() - start_time > timeout:
                raise TimeoutError("Failed to acquire file lock")
            time.sleep(0.01)

        # Create lock file
        self.lock_path.touch()

    def _release_lock(self) -> None:
        """Release file lock by removing lock file."""
        if self.lock_path.exists():
            self.lock_path.unlink()

    def _read_data(self) -> dict:
        """Read all data from the JSON file."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _write_data(self, data: dict) -> None:
        """Write all data to the JSON file."""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def save(self, user_id: str, data: dict) -> None:
        """
        Save or update TOTP data for a user.

        Args:
            user_id: Unique identifier for the user (converted to str)
            data: Dictionary containing TOTP data
        """
        user_id = str(user_id)  # Ensure user_id is string
        try:
            self._acquire_lock()
            all_data = self._read_data()
            all_data[user_id] = data
            self._write_data(all_data)
        finally:
            self._release_lock()

    def get(self, user_id: str) -> Optional[dict]:
        """
        Retrieve TOTP data for a user.

        Args:
            user_id: Unique identifier for the user (converted to str)

        Returns:
            Dictionary containing TOTP data, or None if not found
        """
        user_id = str(user_id)  # Ensure user_id is string
        try:
            self._acquire_lock()
            all_data = self._read_data()
            return all_data.get(user_id)
        finally:
            self._release_lock()

    def delete(self, user_id: str) -> None:
        """
        Delete TOTP data for a user.

        Args:
            user_id: Unique identifier for the user (converted to str)
        """
        user_id = str(user_id)  # Ensure user_id is string
        try:
            self._acquire_lock()
            all_data = self._read_data()
            if user_id in all_data:
                del all_data[user_id]
                self._write_data(all_data)
        finally:
            self._release_lock()

    def exists(self, user_id: str) -> bool:
        """
        Check if TOTP is configured for a user.

        Args:
            user_id: Unique identifier for the user (converted to str)

        Returns:
            True if TOTP data exists, False otherwise
        """
        user_id = str(user_id)  # Ensure user_id is string
        try:
            self._acquire_lock()
            all_data = self._read_data()
            return user_id in all_data
        finally:
            self._release_lock()
