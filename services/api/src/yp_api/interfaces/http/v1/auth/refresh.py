from fastapi import APIRouter, Depends, HTTPException, Request, Response, status, Cookie
from typing import Optional
from pydantic import BaseModel
from yp_api.application.auth.rotate_tokens import RotateTokensUseCase, RotateTokensCommand, InvalidTokenException, TokenReuseException
from yp_api.interfaces.http.dependencies import get_rotate_tokens_use_case

router = APIRouter()

class RefreshResponse(BaseModel):
    data: dict
    meta: dict

@router.post("/refresh")
async def refresh(
    request: Request,
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    use_case: RotateTokensUseCase = Depends(get_rotate_tokens_use_case)
):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "missing_token", "message": "Refresh token cookie is missing"}}
        )
    
    cmd = RotateTokensCommand(refresh_token=refresh_token)
    
    try:
        result = await use_case.execute(cmd)
        
        # Set new Refresh Token in Cookie
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

    except (InvalidTokenException, TokenReuseException) as e:
        # On failure, clear the cookie
        response.delete_cookie(key="refresh_token", path="/v1/auth")
        
        status_code = status.HTTP_401_UNAUTHORIZED
        if isinstance(e, TokenReuseException):
            # We could use 401 or something else, Spec says 401 is common for auth failures
            pass
            
        raise HTTPException(
            status_code=status_code,
            detail={"error": {"code": e.code, "message": str(e)}}
        )

