from typing import List, Dict, Any
from yp_api.domain.services.email import EmailService

class FakeEmailService(EmailService):
    def __init__(self):
        self.sent_emails: List[Dict[str, Any]] = []

    async def send_verification_email(self, email: str, name: str, token: str) -> None:
        self.sent_emails.append({
            "type": "verification",
            "email": email,
            "name": name,
            "token": token
        })

    async def send_password_reset_email(self, email: str, name: str, token: str) -> None:
        self.sent_emails.append({
            "type": "password_reset",
            "email": email,
            "name": name,
            "token": token
        })

    async def send_password_changed_notification(self, email: str, name: str) -> None:
        self.sent_emails.append({
            "type": "password_changed",
            "email": email,
            "name": name
        })

    async def send_login_magic_link(self, email: str, name: str, token: str) -> None:
        self.sent_emails.append({
            "type": "magic_link_login",
            "email": email,
            "name": name,
            "token": token
        })
