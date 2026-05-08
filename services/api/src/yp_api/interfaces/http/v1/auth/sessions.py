from fastapi import APIRouter, Depends, status, Response
from typing import List
from yp_api.domain.users.entities import User as UserEntity
from yp_api.application.auth.list_sessions import ListUserSessionsUseCase, SessionDTO
from yp_api.application.auth.revoke_session import RevokeSessionUseCase, RevokeSessionCommand
from yp_api.interfaces.http.dependencies import get_list_sessions_use_case, get_revoke_session_use_case, get_current_user

router = APIRouter(prefix="/sessions")

@router.get("", response_model=List[SessionDTO])
async def list_sessions(
    user: UserEntity = Depends(get_current_user),
    use_case: ListUserSessionsUseCase = Depends(get_list_sessions_use_case)
):
    return await use_case.execute(user.id)

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_session(
    session_id: str,
    user: UserEntity = Depends(get_current_user),
    use_case: RevokeSessionUseCase = Depends(get_revoke_session_use_case)
):
    cmd = RevokeSessionCommand(session_id=session_id, user_id=user.id)
    await use_case.execute(cmd)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
