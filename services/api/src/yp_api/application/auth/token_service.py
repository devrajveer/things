import os
import secrets
from datetime import datetime, timedelta
import jwt

class TokenService:
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET", "dev_secret_do_not_use_in_prod")
        self.algorithm = "HS256"

    def create_access_token(self, user_id: str, expires_in_seconds: int = 900) -> str:
        now = datetime.utcnow()
        expire = now + timedelta(seconds=expires_in_seconds)
        to_encode = {
            "sub": user_id,
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
            "iss": os.getenv("JWT_ISSUER", "https://api.yourplatform"),
            "aud": "yp-api",
            "jti": secrets.token_urlsafe(16)
        }
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token_string(self) -> str:
        return secrets.token_urlsafe(64)

    def decode_access_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                audience="yp-api",
                issuer=os.getenv("JWT_ISSUER", "https://api.yourplatform")
            )
            return payload
        except jwt.PyJWTError:
            return None
