from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr
from yp_api.application.auth.login_user import LoginUserUseCase, LoginCommand, InvalidCredentialsException
from yp_api.application.auth.rate_limiter import RateLimitExceededException
from yp_api.interfaces.http.dependencies import get_login_use_case

router = APIRouter()

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    data: dict
    meta: dict

@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    response: Response,
    login_req: LoginRequest,
    use_case: LoginUserUseCase = Depends(get_login_use_case)
):
    ip_address = request.client.host
    # Note: In a real prod env behind a proxy, we'd use X-Forwarded-For
    
    cmd = LoginCommand(
        email=login_req.email,
        password=login_req.password,
        ip_address=ip_address
    )
    
    try:
        result = await use_case.execute(cmd)
        
        # Set Refresh Token in Cookie (Security Spec §4.3)
        response.set_cookie(
            key="refresh_token",
            value=result["refresh_token"],
            httponly=True,
            secure=True, # Should be True in prod; FastAPI handles local dev if needed
            samesite="lax",
            max_age=30 * 24 * 60 * 60, # 30 days
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
        
        return LoginResponse(data=data, meta={"request_id": "req_dummy"})

    except InvalidCredentialsException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail={"error": {"code": "invalid_credentials", "message": "Invalid email or password"}}
        )
    except RateLimitExceededException:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, 
            detail={"error": {"code": "rate_limited", "message": "Too many failed attempts. Please try again later."}}
        )
