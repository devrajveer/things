from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from yp_api.application.auth.sign_up_user import SignUpUserUseCase, SignUpCommand, EmailTakenException
from yp_api.domain.users.password_policy import PasswordValidationFailed
from yp_api.interfaces.http.dependencies import get_sign_up_use_case

router = APIRouter()

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    name: str

class SignUpResponse(BaseModel):
    data: dict
    meta: dict

@router.post("/sign-up", response_model=SignUpResponse, status_code=status.HTTP_201_CREATED)
async def sign_up(
    request: SignUpRequest,
    use_case: SignUpUserUseCase = Depends(get_sign_up_use_case)
):
    cmd = SignUpCommand(email=request.email, password=request.password, name=request.name)
    try:
        result = await use_case.execute(cmd)
        
        data = {
            "user": {
                "id": result["user"].id,
                "email": result["user"].email,
                "name": result["user"].name,
                "email_verified": False
            },
            "organization": {
                "id": result["organization"].id,
                "name": result["organization"].name,
                "tier": result["organization"].tier
            },
            "project": {
                "id": result["project"].id,
                "name": result["project"].name
            },
            "tokens": result["tokens"]
        }
        
        return SignUpResponse(data=data, meta={"request_id": "req_dummy"})

    except EmailTakenException:
        raise HTTPException(status_code=409, detail={"error": {"code": "email_taken", "message": "Email already in use"}})
    except PasswordValidationFailed as e:
        raise HTTPException(status_code=422, detail={"error": {"code": "validation_failed", "message": e.message}})
