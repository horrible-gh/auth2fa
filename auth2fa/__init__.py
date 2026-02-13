"""
auth2fa - TOTP-based Two-Factor Authentication Library

A flexible and easy-to-use Python library for implementing TOTP-based
two-factor authentication with support for multiple storage backends.
"""

from .core import TwoFactorAuth
from .storage.base import BaseStorage
from .storage.json_storage import JSONStorage
from .storage.sql_storage import SQLStorage

__version__ = '0.1.2'
__all__ = [
    'TwoFactorAuth',
    'BaseStorage',
    'JSONStorage',
    'SQLStorage'
]

# Optional: Import adapters if sqloader is available
try:
    from .adapters import Auth2FAAdapter
    __all__.append('Auth2FAAdapter')
except ImportError:
    # sqloader is not installed, adapters are not available
    pass
