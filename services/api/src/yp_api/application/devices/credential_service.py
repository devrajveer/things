import secrets
import string
import hashlib
from typing import Tuple

class CredentialService:
    @staticmethod
    def generate_token(length: int = 32) -> str:
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))

    @staticmethod
    def hash_token(token: str) -> str:
        # We use SHA-256 for MQTT/HTTP tokens as they are random long strings
        # and we need fast lookup. For higher security, bcrypt/argon2 could be used
        # but for IoT ingestion performance, salted SHA-256 is often preferred.
        # Here we use a simple SHA-256 for the POC.
        return hashlib.sha256(token.encode()).hexdigest()

    @classmethod
    def generate_device_credentials(cls, device_id: str) -> Tuple[str, str, str, str]:
        """Returns (mqtt_user, mqtt_pass, http_token, mqtt_pass_hash, http_token_hash)"""
        mqtt_user = f"dev_{device_id}"
        mqtt_pass = cls.generate_token()
        http_token = cls.generate_token()
        
        mqtt_pass_hash = cls.hash_token(mqtt_pass)
        http_token_hash = cls.hash_token(http_token)
        
        return mqtt_user, mqtt_pass, http_token, mqtt_pass_hash, http_token_hash
