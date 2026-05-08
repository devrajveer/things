from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from yp_api.application.auth.verify_email import VerifyEmailUseCase, InvalidTokenException, TokenExpiredException
from yp_api.application.auth.resend_verification import ResendVerificationEmailUseCase, RateLimitExceededException
from yp_api.interfaces.http.dependencies_verify import get_verify_email_use_case, get_resend_verification_use_case

router = APIRouter()

class ResendVerificationRequest(BaseModel):
    email: EmailStr

class ResendVerificationResponse(BaseModel):
    data: dict

@router.get("/verify-email")
async def verify_email(
    token: str,
    use_case: VerifyEmailUseCase = Depends(get_verify_email_use_case)
):
    try:
        await use_case.execute(token)
        return RedirectResponse(url="http://localhost:3000/login?verified=true", status_code=302)
    except (InvalidTokenException, TokenExpiredException):
        return RedirectResponse(url="http://localhost:3000/login?error=invalid_token", status_code=302)

@router.post("/verify-email/resend", response_model=ResendVerificationResponse, status_code=status.HTTP_200_OK)
async def resend_verification(
    request: ResendVerificationRequest,
    use_case: ResendVerificationEmailUseCase = Depends(get_resend_verification_use_case)
):
    try:
        await use_case.execute(request.email)
        return ResendVerificationResponse(data={"sent": True})
    except RateLimitExceededException:
        raise HTTPException(status_code=429, detail={"error": {"code": "rate_limited", "message": "Please wait 60s"}})
