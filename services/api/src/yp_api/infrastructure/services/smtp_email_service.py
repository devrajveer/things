import aiosmtplib
from email.message import EmailMessage
from jinja2 import Environment, FileSystemLoader
import os
from yp_api.domain.services.email import EmailService

class SmtpEmailService(EmailService):
    def __init__(self, host: str, port: int, username: str, password: str, from_email: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_email = from_email
        
        # Adjust path depending on execution directory.
        # Assuming run from root of `services/api`
        template_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "templates", "email")
        self.jinja_env = Environment(loader=FileSystemLoader(os.path.abspath(template_dir)))

    async def _send_email(self, to_email: str, subject: str, html_content: str):
        message = EmailMessage()
        message["From"] = self.from_email
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(html_content, subtype="html")

        # Port 587 uses STARTTLS
        use_tls = self.port == 465
        start_tls = self.port == 587
        
        await aiosmtplib.send(
            message,
            hostname=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            use_tls=use_tls,
            start_tls=start_tls,
        )

    async def send_verification_email(self, email: str, name: str, token: str) -> None:
        template = self.jinja_env.get_template("verify_email.html")
        html_content = template.render(name=name, token=token)
        await self._send_email(
            to_email=email,
            subject="Welcome to MegaIoT! Please verify your email.",
            html_content=html_content
        )

    async def send_password_reset_email(self, email: str, name: str, token: str) -> None:
        template = self.jinja_env.get_template("password_reset.html")
        html_content = template.render(name=name, token=token)
        await self._send_email(
            to_email=email,
            subject="Password Reset Request",
            html_content=html_content
        )

    async def send_password_changed_notification(self, email: str, name: str) -> None:
        template = self.jinja_env.get_template("password_changed.html")
        html_content = template.render(name=name)
        await self._send_email(
            to_email=email,
            subject="Your MegaIoT password has been changed",
            html_content=html_content
        )

    async def send_login_magic_link(self, email: str, name: str, token: str) -> None:
        template = self.jinja_env.get_template("magic_link_login.html")
        html_content = template.render(name=name, token=token)
        await self._send_email(
            to_email=email,
            subject="Login to MegaIoT",
            html_content=html_content
        )
