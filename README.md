# auth2fa

A flexible and easy-to-use Python library for implementing TOTP-based two-factor authentication with support for multiple storage backends.

---

## Features

- ✅ TOTP-based 2FA (Time-based One-Time Password)
- ✅ QR code generation for easy setup
- ✅ Recovery codes (8 codes, single-use)
- ✅ Multiple storage backends (JSON file / SQL database)
- ✅ Storage interface for custom backends
- ✅ sqloader integration (optional)
- ✅ No async dependencies - pure synchronous implementation
- ✅ Compatible with Google Authenticator, Authy, etc.

## Installation

### Basic Installation (JSON storage only)

```bash
pip install auth2fa
```

### With SQL Storage Support

```bash
pip install auth2fa[sql]
```

## Quick Start

### JSON Mode (Default)

```python
from auth2fa import TwoFactorAuth

# Initialize with JSON storage (default)
tfa = TwoFactorAuth(issuer="MyApp")

# Setup 2FA for a user
result = tfa.setup("user123", username="john@example.com")
print(result["qr_uri"])          # otpauth:// URI for QR code
print(result["qr_image"])        # Base64 encoded PNG image
print(result["recovery_codes"])  # ['A3F8K2M1', 'B7D2N4P9', ...]

# Activate 2FA (user enters code from authenticator app)
if tfa.activate("user123", "482901"):
    print("2FA activated!")

# Verify during login
if tfa.verify("user123", "173829"):
    print("Login successful!")
```

### SQL Mode (with sqloader)

**Option 1: Using sqloader directly** (if sqloader supports auth2fa's execute interface)

```python
from auth2fa import TwoFactorAuth
from sqloader import SQLite3  # or MySQL

# Initialize database
sq = SQLite3("database.db", sql_path="./auth2fa/sql")

# Initialize with SQL storage
tfa = TwoFactorAuth(sq=sq, issuer="FileForge")

# Rest of the API is the same
result = tfa.setup("user123", username="shin")
tfa.activate("user123", "482901")
tfa.verify("user123", "173829")
```

**Option 2: Using Auth2FAAdapter** (for sqloader's raw database instances)

```python
from auth2fa import TwoFactorAuth, Auth2FAAdapter
from sqloader import SQLiteWrapper  # or MySQLWrapper

# Initialize sqloader database instance
db = SQLiteWrapper('database.db')

# Wrap with adapter
adapter = Auth2FAAdapter(db)

# Initialize with SQL storage
tfa = TwoFactorAuth(sq=adapter, issuer="MyApp")

# Use normally
result = tfa.setup("user123", username="john@example.com")
tfa.activate("user123", "482901")
```

### Custom Storage Path

```python
# Use custom JSON file path
tfa = TwoFactorAuth(storage_path="./data/2fa.json", issuer="MyApp")
```

## API Reference

### TwoFactorAuth

#### `__init__(issuer="MyApp", storage_path=None, sq=None)`

Initialize TwoFactorAuth instance.

**Parameters:**
- `issuer` (str): Application name displayed in authenticator apps
- `storage_path` (str, optional): Path to JSON storage file
- `sq` (optional): sqloader instance for SQL storage

**Storage Priority:**
1. If `sq` is provided → SQL storage
2. If `storage_path` is provided → JSON storage with custom path
3. Otherwise → JSON storage at `./totp_data.json`

#### `setup(user_id, username="")`

Set up TOTP for a user.

**Returns:** dict
```python
{
    "secret": "BASE32SECRET",
    "qr_uri": "otpauth://totp/...",
    "qr_image": "base64encodedPNG...",
    "recovery_codes": ["A3F8K2M1", ...]
}
```

#### `activate(user_id, code)`

Activate TOTP after user verifies the code from their authenticator app.

**Returns:** bool (True if successful)

#### `verify(user_id, code)`

Verify TOTP code during login.

**Behavior:**
- Unconfigured users → returns `True` (pass through)
- Verifies TOTP code first
- If TOTP fails, automatically tries recovery code
- Recovery codes are single-use (automatically removed)

**Returns:** bool

#### `disable(user_id)`

Completely remove TOTP configuration for a user.

#### `is_enabled(user_id)`

Check if TOTP is enabled for a user.

**Returns:** bool

#### `regenerate_recovery_codes(user_id)`

Generate new recovery codes (invalidates old ones).

**Returns:** list

## Integration Example

### Login Flow with 2FA

```python
from auth2fa import TwoFactorAuth

tfa = TwoFactorAuth(issuer="MyApp")

@router.post("/login")
async def login(credentials):
    user = authenticate(credentials)

    if tfa.is_enabled(str(user.id)):
        return {"status": "totp_required", "temp_token": create_temp_token(user)}

    return {"access_token": create_jwt(user)}

@router.post("/login/verify-totp")
async def verify_totp(temp_token, code):
    user = validate_temp_token(temp_token)

    if tfa.verify(str(user.id), code):
        return {"access_token": create_jwt(user)}

    return {"error": "invalid_code"}

@router.post("/user/setup-2fa")
async def setup_2fa(user):
    result = tfa.setup(str(user.id), username=user.email)

    return {
        "qr_image": result["qr_image"],  # Display as <img src="data:image/png;base64,..." />
        "recovery_codes": result["recovery_codes"]  # Show to user (print/save)
    }

@router.post("/user/activate-2fa")
async def activate_2fa(user, code):
    if tfa.activate(str(user.id), code):
        return {"success": True}
    return {"error": "invalid_code"}

@router.post("/user/disable-2fa")
async def disable_2fa(user):
    tfa.disable(str(user.id))
    return {"success": True}
```

## Storage Backends

### JSON Storage (Default)

- File-based storage with file locking
- Default path: `./totp_data.json`
- Thread-safe with lock file mechanism
- Auto-converts user_id to string

### SQL Storage (with sqloader)

Requires `auth2fa[sql]` installation.

**Supported Databases:**
- SQLite3
- MySQL
- PostgreSQL (via sqloader)

**Table Schema:**
```sql
CREATE TABLE totp_auth (
    user_id VARCHAR(255) PRIMARY KEY,
    secret VARCHAR(255) NOT NULL,
    enabled BOOLEAN DEFAULT FALSE,
    recovery_codes TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_totp_auth_enabled ON totp_auth(enabled);
```

**Database Compatibility:**
- ✅ SQLite3
- ✅ MySQL / MariaDB
- ✅ PostgreSQL

#### Auth2FAAdapter

The `Auth2FAAdapter` is an optional adapter that bridges auth2fa with sqloader's database instances. It's automatically available when sqloader is installed.

**Features:**
- 🔄 Automatic SQL file loading from `auth2fa/sql` directory
- 🔀 Parameter binding conversion (SQLite `:param` vs MySQL `%s`)
- 🗃️ SQL dialect conversion (PostgreSQL `ON CONFLICT` vs MySQL `ON DUPLICATE KEY UPDATE`)
- 📊 Support for both SELECT and DML statements

**When to use:**
- You're using sqloader's `SQLiteWrapper` or `MySQLWrapper` directly
- You need automatic database dialect conversion
- You want to avoid sqloader dependency in auth2fa core

**Example:**
```python
from auth2fa import Auth2FAAdapter
from sqloader import SQLiteWrapper

# Your existing sqloader setup
db = SQLiteWrapper('app.db')

# Wrap it for auth2fa
adapter = Auth2FAAdapter(db)

# Use with TwoFactorAuth
from auth2fa import TwoFactorAuth
tfa = TwoFactorAuth(sq=adapter, issuer="MyApp")
```

**Without sqloader:**
If sqloader is not installed, `Auth2FAAdapter` won't be available, but auth2fa will still work with JSON storage:
```python
from auth2fa import TwoFactorAuth

# Falls back to JSON storage
tfa = TwoFactorAuth(issuer="MyApp")  # Uses ./totp_data.json
```

### Custom Storage Backend

Implement `BaseStorage` interface:

```python
from auth2fa.storage.base import BaseStorage

class CustomStorage(BaseStorage):
    def save(self, user_id: str, data: dict) -> None:
        # Your implementation
        pass

    def get(self, user_id: str) -> dict | None:
        # Your implementation
        pass

    def delete(self, user_id: str) -> None:
        # Your implementation
        pass

    def exists(self, user_id: str) -> bool:
        # Your implementation
        pass

# Use custom storage
from auth2fa import TwoFactorAuth
tfa = TwoFactorAuth.__new__(TwoFactorAuth)
tfa.issuer = "MyApp"
tfa.storage = CustomStorage()
```

## Data Structure

TOTP data stored for each user:

```python
{
    "secret": "BASE32SECRET",           # TOTP secret key
    "enabled": False,                   # Activation status
    "recovery_codes": [                 # Single-use backup codes
        "A3F8K2M1",
        "B7D2N4P9",
        # ... 8 codes total
    ],
    "created_at": "2026-02-11T18:00:00"  # ISO format timestamp
}
```

## Security Notes

- Recovery codes are alphanumeric (excluding 0, O, I, 1 for clarity)
- TOTP uses 30-second time window with ±1 window tolerance
- Recovery codes are case-insensitive
- Each recovery code can only be used once
- File locking prevents race conditions in JSON storage

## Requirements

- Python 3.10+
- pyotp
- qrcode
- Pillow

**Optional:**
- sqloader (for SQL storage)

## License

MIT License

## Links

- **Homepage**: https://github.com/horrible-gh/auth2fa
- **Bug Tracker**: https://github.com/horrible-gh/auth2fa/issues

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
