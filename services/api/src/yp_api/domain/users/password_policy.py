import os
import re

class PasswordValidationFailed(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

def _load_common_passwords() -> set[str]:
    # Try to load from packages/sec-data or fallback to empty set
    try:
        path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "packages", "sec-data", "common-passwords.txt")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return set(line.strip() for line in f if line.strip())
    except Exception:
        pass
    return set()

COMMON_PASSWORDS = _load_common_passwords()

def validate_password(password: str) -> None:
    if len(password) < 12:
        raise PasswordValidationFailed("Password must be at least 12 characters long")
    
    types_count = 0
    if re.search(r'[A-Z]', password):
        types_count += 1
    if re.search(r'[a-z]', password):
        types_count += 1
    if re.search(r'[0-9]', password):
        types_count += 1
    if re.search(r'[^A-Za-z0-9]', password):
        types_count += 1
        
    if types_count < 3:
        raise PasswordValidationFailed("Password must contain at least 3 of: lowercase, uppercase, digit, symbol")
        
    if password in COMMON_PASSWORDS:
        raise PasswordValidationFailed("Password is too common")
