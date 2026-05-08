import os
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16
)

class Argon2PasswordHasher:
    def __init__(self):
        self._pepper = os.getenv("PASSWORD_PEPPER", "")

    def _apply_pepper(self, password: str) -> str:
        return password + self._pepper

    def hash_password(self, password: str) -> str:
        return hasher.hash(self._apply_pepper(password))

    def verify_password(self, password: str, hash_string: str) -> bool:
        try:
            return hasher.verify(hash_string, self._apply_pepper(password))
        except VerifyMismatchError:
            return False

    def needs_rehash(self, hash_string: str) -> bool:
        return hasher.check_needs_rehash(hash_string)
