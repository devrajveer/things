from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
from yp_api.domain.users.entities import User
from yp_api.interfaces.http.dependencies import get_current_user, get_uow
from yp_api.domain.automation.entities import Rule, Webhook, RuleOperator
import uuid
import secrets

router = APIRouter()

# --- Schemas ---

class RuleResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    stream_id: Optional[str] = None
    condition: Dict[str, Any]
    actions: List[Dict[str, Any]]
    is_enabled: bool

class CreateRuleRequest(BaseModel):
    name: str
    description: Optional[str] = None
    stream_id: Optional[str] = None
    condition: Dict[str, Any]
    actions: List[Dict[str, Any]]
    is_enabled: bool = True

class WebhookResponse(BaseModel):
    id: str
    name: str
    url: str
    secret: str
    is_enabled: bool

class CreateWebhookRequest(BaseModel):
    name: str
    url: str
    is_enabled: bool = True

# --- Rules Endpoints ---

@router.get("/rules", response_model=List[RuleResponse])
async def list_rules(
    project_id: str,
    user: User = Depends(get_current_user),
    uow = Depends(get_uow)
):
    async with uow:
        rules = await uow.rules.list_by_project(project_id)
        return [RuleResponse(**r.__dict__) for r in rules]

@router.post("/rules", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    project_id: str,
    request: CreateRuleRequest,
    user: User = Depends(get_current_user),
    uow = Depends(get_uow)
):
    async with uow:
        rule = Rule(
            id=f"rul_{uuid.uuid4().hex[:12]}",
            project_id=project_id,
            stream_id=request.stream_id,
            name=request.name,
            description=request.description,
            condition=request.condition,
            actions=request.actions,
            is_enabled=request.is_enabled
        )
        await uow.rules.save(rule)
        await uow.commit()
        return RuleResponse(**rule.__dict__)

@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    project_id: str,
    rule_id: str,
    user: User = Depends(get_current_user),
    uow = Depends(get_uow)
):
    async with uow:
        await uow.rules.delete(rule_id)
        await uow.commit()

# --- Webhooks Endpoints ---

@router.get("/webhooks", response_model=List[WebhookResponse])
async def list_webhooks(
    project_id: str,
    user: User = Depends(get_current_user),
    uow = Depends(get_uow)
):
    async with uow:
        webhooks = await uow.webhooks.list_by_project(project_id)
        return [WebhookResponse(**w.__dict__) for w in webhooks]

@router.post("/webhooks", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    project_id: str,
    request: CreateWebhookRequest,
    user: User = Depends(get_current_user),
    uow = Depends(get_uow)
):
    async with uow:
        webhook = Webhook(
            id=f"whk_{uuid.uuid4().hex[:12]}",
            project_id=project_id,
            name=request.name,
            url=str(request.url),
            secret=secrets.token_hex(20),
            is_enabled=request.is_enabled
        )
        await uow.webhooks.save(webhook)
        await uow.commit()
        return WebhookResponse(**webhook.__dict__)

@router.delete("/webhooks/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    project_id: str,
    webhook_id: str,
    user: User = Depends(get_current_user),
    uow = Depends(get_uow)
):
    async with uow:
        await uow.webhooks.delete(webhook_id)
        await uow.commit()
