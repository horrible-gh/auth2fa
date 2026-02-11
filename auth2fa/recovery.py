"""Recovery code generation and verification for auth2fa."""
import secrets
import string
from typing import List, Tuple


def generate_recovery_codes(count: int = 8, length: int = 8) -> List[str]:
    """
    Generate a list of random recovery codes.

    Args:
        count: Number of recovery codes to generate (default: 8)
        length: Length of each recovery code (default: 8)

    Returns:
        List of recovery codes in format like ['A3F8K2M1', 'B7D2N4P9', ...]
    """
    codes = []
    # Use alphanumeric characters excluding similar-looking ones (0, O, I, 1)
    alphabet = string.ascii_uppercase + string.digits
    alphabet = alphabet.replace('0', '').replace('O', '').replace('I', '').replace('1', '')

    for _ in range(count):
        code = ''.join(secrets.choice(alphabet) for _ in range(length))
        codes.append(code)

    return codes


def verify_recovery_code(stored_codes: List[str], input_code: str) -> Tuple[bool, List[str]]:
    """
    Verify if a recovery code is valid and return updated code list.

    Args:
        stored_codes: List of valid recovery codes
        input_code: The recovery code to verify

    Returns:
        Tuple of (is_valid, updated_codes):
        - (True, codes with used code removed) if valid
        - (False, original codes) if invalid

    Recovery codes are single-use — successful verification removes the code.
    """
    # Case-insensitive comparison
    input_upper = input_code.upper()
    codes_upper = [rc.upper() for rc in stored_codes]

    if input_upper in codes_upper:
        # Remove the used code
        updated_codes = [rc for rc in stored_codes if rc.upper() != input_upper]
        return (True, updated_codes)
    else:
        return (False, stored_codes)
