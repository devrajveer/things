class AppError(Exception):
    """Base exception for application errors."""
    code: str = "internal_error"
    
    def __init__(self, message: str, details: dict[str, str] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

class NotFoundError(AppError):
    code = "not_found"

class ValidationError(AppError):
    code = "validation_error"

class AuthenticationError(AppError):
    code = "unauthorized"

class AuthorizationError(AppError):
    code = "forbidden"

class QuotaExceededError(AppError):
    code = "quota_exceeded"
