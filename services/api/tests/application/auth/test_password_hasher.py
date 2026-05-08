import pytest
from yp_api.application.auth.password_hasher import Argon2PasswordHasher
import time

def test_password_hashing():
    hasher = Argon2PasswordHasher()
    pwd = "Correct-Horse-Battery-Staple!"

    start = time.time()
    hashed = hasher.hash_password(pwd)
    duration = time.time() - start

    assert duration > 0.05
    assert duration < 0.6  # Playbook wants < 500ms but leaving some buffer for slow CI
    
    assert hasher.verify_password(pwd, hashed) is True
    assert hasher.verify_password("wrong", hashed) is False
