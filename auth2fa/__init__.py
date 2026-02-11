"""
auth2fa - TOTP-based Two-Factor Authentication Library

A flexible and easy-to-use Python library for implementing TOTP-based
two-factor authentication with support for multiple storage backends.
"""

from .core import TwoFactorAuth
from .storage.base import BaseStorage
from .storage.json_storage import JSONStorage
from .storage.sql_storage import SQLStorage

__version__ = '0.1.0'
__all__ = [
    'TwoFactorAuth',
    'BaseStorage',
    'JSONStorage',
    'SQLStorage'
]
