from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from yp_api.domain.users.entities import User
from yp_api.interfaces.http.dependencies import (
    get_current_user,
    get_list_orgs_use_case,
    get_org_use_case,
    get_create_org_use_case,
    get_update_org_use_case,
    get_delete_org_use_case
)
from yp_api.application.organizations.get_org import GetOrganizationUseCase, OrganizationNotFound, OrganizationAccessDenied
from yp_api.application.organizations.list_orgs import ListOrganizationsUseCase
from yp_api.application.organizations.create_org import CreateOrganizationUseCase, CreateOrganizationCommand
from yp_api.application.organizations.update_org import UpdateOrganizationUseCase, UpdateOrganizationCommand, OrganizationUpdateForbidden
from yp_api.application.organizations.delete_org import DeleteOrganizationUseCase, OrganizationDeleteForbidden

router = APIRouter()

class OrganizationResponse(BaseModel):
    id: str
    name: str
    tier: str
    created_at: Optional[datetime]

class OrganizationListResponse(BaseModel):
    data: List[OrganizationResponse]
    meta: dict = {}

class OrganizationSingleResponse(BaseModel):
    data: OrganizationResponse
    meta: dict = {}

class CreateOrgRequest(BaseModel):
    name: str

class UpdateOrgRequest(BaseModel):
    name: Optional[str] = None

@router.get("", response_model=OrganizationListResponse)
async def list_organizations(
    user: User = Depends(get_current_user),
    use_case: ListOrganizationsUseCase = Depends(get_list_orgs_use_case)
):
    orgs = await use_case.execute(user.id)
    return OrganizationListResponse(
        data=[
            OrganizationResponse(
                id=o.id, name=o.name, tier=o.tier, created_at=o.created_at
            ) for o in orgs
        ]
    )

@router.post("", response_model=OrganizationSingleResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    request: CreateOrgRequest,
    user: User = Depends(get_current_user),
    use_case: CreateOrganizationUseCase = Depends(get_create_org_use_case)
):
    cmd = CreateOrganizationCommand(name=request.name)
    org = await use_case.execute(user.id, cmd)
    return OrganizationSingleResponse(
        data=OrganizationResponse(id=org.id, name=org.name, tier=org.tier, created_at=org.created_at)
    )

@router.get("/{org_id}", response_model=OrganizationSingleResponse)
async def get_organization(
    org_id: str,
    user: User = Depends(get_current_user),
    use_case: GetOrganizationUseCase = Depends(get_org_use_case)
):
    try:
        org = await use_case.execute(org_id, user.id)
        return OrganizationSingleResponse(
            data=OrganizationResponse(id=org.id, name=org.name, tier=org.tier, created_at=org.created_at)
        )
    except OrganizationNotFound:
        raise HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": "Organization not found"}})
    except OrganizationAccessDenied:
        raise HTTPException(status_code=403, detail={"error": {"code": "forbidden", "message": "Access denied"}})

@router.patch("/{org_id}", response_model=OrganizationSingleResponse)
async def update_organization(
    org_id: str,
    request: UpdateOrgRequest,
    user: User = Depends(get_current_user),
    use_case: UpdateOrganizationUseCase = Depends(get_update_org_use_case)
):
    if not request.name:
        raise HTTPException(status_code=422, detail={"error": {"code": "validation_failed", "message": "Name is required for update"}})
        
    cmd = UpdateOrganizationCommand(name=request.name)
    try:
        org = await use_case.execute(org_id, user.id, cmd)
        return OrganizationSingleResponse(
            data=OrganizationResponse(id=org.id, name=org.name, tier=org.tier, created_at=org.created_at)
        )
    except OrganizationNotFound:
        raise HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": "Organization not found"}})
    except OrganizationUpdateForbidden as e:
        raise HTTPException(status_code=403, detail={"error": {"code": "forbidden", "message": str(e)}})

@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    org_id: str,
    user: User = Depends(get_current_user),
    use_case: DeleteOrganizationUseCase = Depends(get_delete_org_use_case)
):
    try:
        await use_case.execute(org_id, user.id)
    except OrganizationNotFound:
        raise HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": "Organization not found"}})
    except OrganizationDeleteForbidden as e:
        raise HTTPException(status_code=403, detail={"error": {"code": "forbidden", "message": str(e)}})

from yp_api.application.organizations.invite_member import InviteMemberUseCase, InviteMemberCommand, InviteMemberForbidden
from yp_api.application.organizations.accept_invite import AcceptInviteUseCase, AcceptInviteCommand, InvalidInvite
from yp_api.application.organizations.update_member import UpdateMemberUseCase, UpdateMemberCommand, UpdateMemberForbidden
from yp_api.application.organizations.remove_member import RemoveMemberUseCase, RemoveMemberForbidden
from yp_api.application.organizations.list_members import ListMembersUseCase, ListMembersForbidden
from yp_api.application.organizations.list_invites import ListInvitesUseCase, ListInvitesForbidden
from yp_api.interfaces.http.dependencies import (
    get_invite_member_use_case,
    get_accept_invite_use_case,
    get_update_member_use_case,
    get_remove_member_use_case,
    get_list_members_use_case,
    get_list_invites_use_case
)

class InviteMemberRequest(BaseModel):
    email: str
    role: str

class AcceptInviteRequest(BaseModel):
    token: str

class UpdateMemberRequest(BaseModel):
    role: str

class MemberResponse(BaseModel):
    user_id: str
    role: str
    created_at: Optional[datetime]

class InviteResponse(BaseModel):
    id: str
    email: str
    role: str
    expires_at: datetime
    accepted_at: Optional[datetime]

@router.get("/{org_id}/members", response_model=dict)
async def list_members(
    org_id: str,
    user: User = Depends(get_current_user),
    use_case: ListMembersUseCase = Depends(get_list_members_use_case)
):
    try:
        members = await use_case.execute(org_id, user.id)
        return {"data": [MemberResponse(user_id=m.user_id, role=m.role, created_at=m.created_at).model_dump() for m in members]}
    except ListMembersForbidden as e:
        raise HTTPException(status_code=403, detail={"error": {"code": "forbidden", "message": str(e)}})

@router.patch("/{org_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_member(
    org_id: str,
    user_id: str,
    request: UpdateMemberRequest,
    user: User = Depends(get_current_user),
    use_case: UpdateMemberUseCase = Depends(get_update_member_use_case)
):
    cmd = UpdateMemberCommand(role=request.role)
    try:
        await use_case.execute(org_id, user.id, user_id, cmd)
    except UpdateMemberForbidden as e:
        raise HTTPException(status_code=403, detail={"error": {"code": "forbidden", "message": str(e)}})

@router.delete("/{org_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    org_id: str,
    user_id: str,
    user: User = Depends(get_current_user),
    use_case: RemoveMemberUseCase = Depends(get_remove_member_use_case)
):
    try:
        await use_case.execute(org_id, user.id, user_id)
    except RemoveMemberForbidden as e:
        raise HTTPException(status_code=403, detail={"error": {"code": "forbidden", "message": str(e)}})

@router.get("/{org_id}/invites", response_model=dict)
async def list_invites(
    org_id: str,
    user: User = Depends(get_current_user),
    use_case: ListInvitesUseCase = Depends(get_list_invites_use_case)
):
    try:
        invites = await use_case.execute(org_id, user.id)
        return {"data": [InviteResponse(id=i.id, email=i.email, role=i.role, expires_at=i.expires_at, accepted_at=i.accepted_at).model_dump() for i in invites]}
    except ListInvitesForbidden as e:
        raise HTTPException(status_code=403, detail={"error": {"code": "forbidden", "message": str(e)}})

@router.post("/{org_id}/invites", status_code=status.HTTP_201_CREATED)
async def invite_member(
    org_id: str,
    request: InviteMemberRequest,
    user: User = Depends(get_current_user),
    use_case: InviteMemberUseCase = Depends(get_invite_member_use_case)
):
    cmd = InviteMemberCommand(email=request.email, role=request.role)
    try:
        res = await use_case.execute(org_id, user.id, cmd)
        return {"data": res}
    except InviteMemberForbidden as e:
        raise HTTPException(status_code=403, detail={"error": {"code": "forbidden", "message": str(e)}})

@router.post("/invites/accept", status_code=status.HTTP_200_OK)
async def accept_invite(
    request: AcceptInviteRequest,
    user: User = Depends(get_current_user),
    use_case: AcceptInviteUseCase = Depends(get_accept_invite_use_case)
):
    cmd = AcceptInviteCommand(token=request.token)
    try:
        org_id = await use_case.execute(user.id, user.email, cmd)
        return {"data": {"org_id": org_id}}
    except InvalidInvite as e:
        raise HTTPException(status_code=400, detail={"error": {"code": "invalid_invite", "message": str(e)}})
