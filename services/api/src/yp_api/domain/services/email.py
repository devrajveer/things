from typing import Protocol

class EmailService(Protocol):
    async def send_verification_email(self, email: str, name: str, token: str) -> None:
        ...

    async def send_password_reset_email(self, email: str, name: str, token: str) -> None:
        ...

    async def send_password_changed_notification(self, email: str, name: str) -> None:
        ...

    async def send_login_magic_link(self, email: str, name: str, token: str) -> None:
        ...
