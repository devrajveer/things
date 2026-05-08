from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, EmailStr
from yp_api.application.auth.request_password_reset import RequestPasswordResetUseCase, RequestPasswordResetCommand
from yp_api.application.auth.reset_password import ResetPasswordUseCase, ResetPasswordCommand
from yp_api.interfaces.http.dependencies import get_request_password_reset_use_case, get_reset_password_use_case

router = APIRouter(prefix="/password-reset")

class RequestResetRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

@router.post("/request", status_code=status.HTTP_202_ACCEPTED)
async def request_password_reset(
    req: RequestResetRequest,
    use_case: RequestPasswordResetUseCase = Depends(get_request_password_reset_use_case)
):
    cmd = RequestPasswordResetCommand(email=req.email)
    await use_case.execute(cmd)
    return {"message": "If an account exists with that email, a password reset link has been sent."}

@router.post("/reset")
async def reset_password(
    req: ResetPasswordRequest,
    use_case: ResetPasswordUseCase = Depends(get_reset_password_use_case)
):
    cmd = ResetPasswordCommand(token=req.token, new_password=req.new_password)
    await use_case.execute(cmd)
    return {"message": "Your password has been successfully reset."}
