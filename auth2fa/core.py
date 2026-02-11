"""Core TOTP authentication logic for auth2fa."""
import base64
import pyotp
import qrcode
from io import BytesIO
from datetime import datetime
from typing import Optional, Dict
from .storage.base import BaseStorage
from .storage.json_storage import JSONStorage
from .storage.sql_storage import SQLStorage
from .recovery import generate_recovery_codes, verify_recovery_code


class TwoFactorAuth:
    """Main class for TOTP-based two-factor authentication."""

    def __init__(self, issuer: str = "MyApp", storage_path: Optional[str] = None, sq=None):
        """
        Initialize TwoFactorAuth.

        Args:
            issuer: Name of the application/service for TOTP
            storage_path: Path to JSON storage file (optional)
            sq: sqloader instance for SQL storage (optional)

        Initialization priority:
        1. If sq is provided → SQLStorage
        2. If storage_path is provided → JSONStorage with custom path
        3. Otherwise → JSONStorage with default path ("./totp_data.json")
        """
        self.issuer = issuer

        # Determine storage backend based on priority
        if sq is not None:
            self.storage = SQLStorage(sq)
        elif storage_path is not None:
            self.storage = JSONStorage(storage_path)
        else:
            self.storage = JSONStorage("./totp_data.json")

    def setup(self, user_id: str, username: str = "") -> Dict:
        """
        Set up TOTP for a user.

        Args:
            user_id: Unique identifier for the user
            username: Display name for the account (defaults to empty string)

        Returns:
            Dictionary containing:
            {
                "secret": "BASE32SECRET",
                "qr_uri": "otpauth://totp/Issuer:username?secret=...&issuer=...",
                "qr_image": "base64 encoded PNG QR image",
                "recovery_codes": ["A3F8K2M1", ...]
            }
        """
        user_id = str(user_id)  # Ensure user_id is string

        if self.storage.exists(user_id):
            raise ValueError(f"TOTP already configured for user: {user_id}")

        # Generate secret and recovery codes
        secret = pyotp.random_base32()
        recovery_codes = generate_recovery_codes(count=8, length=8)

        # Generate provisioning URI for QR code
        account_name = username if username else user_id
        totp = pyotp.TOTP(secret)
        qr_uri = totp.provisioning_uri(
            name=account_name,
            issuer_name=self.issuer
        )

        # Generate QR code image
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_image_bytes = buffer.getvalue()
        qr_image_base64 = base64.b64encode(qr_image_bytes).decode('utf-8')

        # Save to storage (not enabled yet)
        data = {
            'secret': secret,
            'enabled': False,
            'recovery_codes': recovery_codes,
            'created_at': datetime.now().isoformat()
        }
        self.storage.save(user_id, data)

        return {
            "secret": secret,
            "qr_uri": qr_uri,
            "qr_image": qr_image_base64,
            "recovery_codes": recovery_codes
        }

    def activate(self, user_id: str, code: str) -> bool:
        """
        Activate TOTP after user verifies the code from their app.

        Args:
            user_id: Unique identifier for the user
            code: TOTP code from authenticator app

        Returns:
            True if activation successful, False if code is invalid
        """
        user_id = str(user_id)  # Ensure user_id is string

        data = self.storage.get(user_id)
        if not data:
            raise ValueError(f"TOTP not configured for user: {user_id}")

        if data['enabled']:
            raise ValueError(f"TOTP already activated for user: {user_id}")

        # Verify the token
        secret = data['secret']
        totp = pyotp.TOTP(secret)
        if totp.verify(code, valid_window=1):
            data['enabled'] = True
            self.storage.save(user_id, data)
            return True

        return False

    def verify(self, user_id: str, code: str) -> bool:
        """
        Verify TOTP code during login.

        Args:
            user_id: Unique identifier for the user
            code: TOTP code or recovery code

        Returns:
            True if verification successful, False otherwise

        Behavior:
        - Unconfigured user → True (pass through)
        - TOTP code verification (valid_window=1)
        - If TOTP fails, try recovery code
        - Recovery code used → automatically removed
        """
        user_id = str(user_id)  # Ensure user_id is string

        data = self.storage.get(user_id)

        # Unconfigured user → pass through
        if not data:
            return True

        # Try TOTP code first
        secret = data['secret']
        totp = pyotp.TOTP(secret)
        if totp.verify(code, valid_window=1):
            return True

        # TOTP failed, try recovery code
        recovery_codes = data.get('recovery_codes', [])
        is_valid, updated_codes = verify_recovery_code(recovery_codes, code)

        if is_valid:
            # Update storage with used code removed
            data['recovery_codes'] = updated_codes
            self.storage.save(user_id, data)
            return True

        return False

    def disable(self, user_id: str) -> None:
        """
        Disable and remove TOTP configuration for a user.

        Args:
            user_id: Unique identifier for the user
        """
        user_id = str(user_id)  # Ensure user_id is string
        self.storage.delete(user_id)

    def is_enabled(self, user_id: str) -> bool:
        """
        Check if TOTP is enabled for a user.

        Args:
            user_id: Unique identifier for the user

        Returns:
            True if TOTP is enabled, False otherwise
        """
        user_id = str(user_id)  # Ensure user_id is string

        data = self.storage.get(user_id)
        if not data:
            return False
        return data.get('enabled', False)

    def regenerate_recovery_codes(self, user_id: str) -> list:
        """
        Regenerate recovery codes for a user.

        Args:
            user_id: Unique identifier for the user

        Returns:
            List of new recovery codes
        """
        user_id = str(user_id)  # Ensure user_id is string

        data = self.storage.get(user_id)
        if not data:
            raise ValueError(f"TOTP not configured for user: {user_id}")

        new_codes = generate_recovery_codes(count=8, length=8)
        data['recovery_codes'] = new_codes
        self.storage.save(user_id, data)

        return new_codes
