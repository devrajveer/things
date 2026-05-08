from fastapi import APIRouter, Depends, Response, status, Query, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from yp_api.application.auth.request_magic_link import RequestMagicLinkUseCase, RequestMagicLinkCommand
from yp_api.application.auth.verify_magic_link import VerifyMagicLinkUseCase, VerifyMagicLinkCommand, InvalidMagicLinkException
from yp_api.interfaces.http.dependencies import get_request_magic_link_use_case, get_verify_magic_link_use_case

router = APIRouter(prefix="/magic-link")

class RequestMagicLinkRequest(BaseModel):
    email: EmailStr

@router.post("/request", status_code=status.HTTP_202_ACCEPTED)
async def request_magic_link(
    req: RequestMagicLinkRequest,
    use_case: RequestMagicLinkUseCase = Depends(get_request_magic_link_use_case)
):
    cmd = RequestMagicLinkCommand(email=req.email)
    await use_case.execute(cmd)
    return {"message": "If an account exists with that email, a login link has been sent."}

@router.get("/verify")
async def verify_magic_link(
    response: Response,
    token: str = Query(...),
    use_case: VerifyMagicLinkUseCase = Depends(get_verify_magic_link_use_case)
):
    cmd = VerifyMagicLinkCommand(token=token)
    
    try:
        result = await use_case.execute(cmd)
        
        # Set Refresh Token in Cookie
        response.set_cookie(
            key="refresh_token",
            value=result["refresh_token"],
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=30 * 24 * 60 * 60,
            path="/v1/auth"
        )
        
        data = {
            "access_token": result["access_token"],
            "expires_in": result["expires_in"],
            "user": {
                "id": result["user"].id,
                "email": result["user"].email,
                "name": result["user"].name
            }
        }
        
        return {"data": data, "meta": {"request_id": "req_dummy"}}

    except InvalidMagicLinkException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": e.code, "message": str(e)}}
        )

