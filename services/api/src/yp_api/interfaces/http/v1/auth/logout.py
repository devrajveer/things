from fastapi import APIRouter, Depends, Response, Cookie, status
from pydantic import BaseModel
from typing import Optional
from yp_api.application.auth.logout_user import LogoutUserUseCase, LogoutCommand
from yp_api.interfaces.http.dependencies import get_logout_use_case

router = APIRouter()

class LogoutRequest(BaseModel):
    global_logout: bool = False

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    logout_req: Optional[LogoutRequest] = None,
    refresh_token: Optional[str] = Cookie(None),
    use_case: LogoutUserUseCase = Depends(get_logout_use_case)
):
    # Execute logout logic
    cmd = LogoutCommand(
        refresh_token=refresh_token,
        global_logout=logout_req.global_logout if logout_req else False
    )
    await use_case.execute(cmd)
    
    # Always clear the cookie
    response.delete_cookie(
        key="refresh_token",
        path="/v1/auth"
    )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)
