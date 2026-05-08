from fastapi import Request
from yp_api.application.auth.verify_email import VerifyEmailUseCase
from yp_api.application.auth.resend_verification import ResendVerificationEmailUseCase
from yp_api.application.auth.password_hasher import Argon2PasswordHasher
from yp_api.infrastructure.persistence.uow import SQLAlchemyUnitOfWork
from yp_api.interfaces.http.dependencies import get_email_service

def get_verify_email_use_case(request: Request) -> VerifyEmailUseCase:
    session_maker = getattr(request.app.state, "db_session_maker", lambda: None)
    uow = SQLAlchemyUnitOfWork(session_maker)
    password_hasher = Argon2PasswordHasher()
    return VerifyEmailUseCase(uow, password_hasher)

def get_resend_verification_use_case(request: Request) -> ResendVerificationEmailUseCase:
    session_maker = getattr(request.app.state, "db_session_maker", lambda: None)
    uow = SQLAlchemyUnitOfWork(session_maker)
    password_hasher = Argon2PasswordHasher()
    return ResendVerificationEmailUseCase(uow, password_hasher, get_email_service())
