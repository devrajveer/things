from typing import Optional, List
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from yp_api.domain.automation.entities import Rule, Webhook
from yp_api.models.core import Rule as RuleModel, Webhook as WebhookModel

class SQLRuleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, id: str) -> Optional[Rule]:
        stmt = select(RuleModel).where(RuleModel.id == id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            return self._to_entity(model)
        return None

    async def save(self, rule: Rule) -> Rule:
        stmt = select(RuleModel).where(RuleModel.id == rule.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.name = rule.name
            model.description = rule.description
            model.condition = rule.condition
            model.actions = rule.actions
            model.is_enabled = rule.is_enabled
            model.stream_id = rule.stream_id
            model.updated_at = rule.updated_at
        else:
            model = RuleModel(
                id=rule.id,
                project_id=rule.project_id,
                stream_id=rule.stream_id,
                name=rule.name,
                description=rule.description,
                condition=rule.condition,
                actions=rule.actions,
                is_enabled=rule.is_enabled,
                created_at=rule.created_at,
                updated_at=rule.updated_at
            )
            self.session.add(model)
        
        return rule

    async def list_by_project(self, project_id: str) -> List[Rule]:
        stmt = select(RuleModel).where(RuleModel.project_id == project_id).order_by(RuleModel.created_at.desc())
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_by_stream(self, stream_id: str) -> List[Rule]:
        stmt = select(RuleModel).where(RuleModel.stream_id == stream_id, RuleModel.is_enabled == True)
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def delete(self, id: str) -> None:
        stmt = delete(RuleModel).where(RuleModel.id == id)
        await self.session.execute(stmt)

    def _to_entity(self, model: RuleModel) -> Rule:
        return Rule(
            id=model.id,
            project_id=model.project_id,
            stream_id=model.stream_id,
            name=model.name,
            description=model.description,
            condition=model.condition,
            actions=model.actions,
            is_enabled=model.is_enabled,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

class SQLWebhookRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, id: str) -> Optional[Webhook]:
        stmt = select(WebhookModel).where(WebhookModel.id == id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            return self._to_entity(model)
        return None

    async def save(self, webhook: Webhook) -> Webhook:
        stmt = select(WebhookModel).where(WebhookModel.id == webhook.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.name = webhook.name
            model.url = webhook.url
            model.secret = webhook.secret
            model.is_enabled = webhook.is_enabled
            model.updated_at = webhook.updated_at
        else:
            model = WebhookModel(
                id=webhook.id,
                project_id=webhook.project_id,
                name=webhook.name,
                url=webhook.url,
                secret=webhook.secret,
                is_enabled=webhook.is_enabled,
                created_at=webhook.created_at,
                updated_at=webhook.updated_at
            )
            self.session.add(model)
        
        return webhook

    async def list_by_project(self, project_id: str) -> List[Webhook]:
        stmt = select(WebhookModel).where(WebhookModel.project_id == project_id).order_by(WebhookModel.created_at.desc())
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def delete(self, id: str) -> None:
        stmt = delete(WebhookModel).where(WebhookModel.id == id)
        await self.session.execute(stmt)

    def _to_entity(self, model: WebhookModel) -> Webhook:
        return Webhook(
            id=model.id,
            project_id=model.project_id,
            name=model.name,
            url=model.url,
            secret=model.secret,
            is_enabled=model.is_enabled,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
