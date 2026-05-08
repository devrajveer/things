from enum import Enum
from typing import Set, Dict, Optional
from pydantic import BaseModel

class ProjectPermission(str, Enum):
    PROJECT_VIEW = "project.view" # Not in audit actions, but needed for GET
    PROJECT_CREATE = "project.created"
    PROJECT_UPDATE = "project.updated"
    PROJECT_DELETE = "project.deleted"
    
    DEVICE_CREATE = "device.created"
    DEVICE_UPDATE = "device.updated"
    DEVICE_DELETE = "device.deleted"
    DEVICE_DISABLE = "device.disabled"
    DEVICE_ENABLE = "device.enabled"
    DEVICE_ROTATE_CREDS = "device.token_rotated"
    
    RULE_CREATE = "rule.created"
    RULE_UPDATE = "rule.updated"
    RULE_DELETE = "rule.deleted"
    RULE_ENABLE = "rule.enabled"
    RULE_DISABLE = "rule.disabled"
    
    ALERT_ACK = "alert.acknowledged"
    ALERT_RESOLVE = "alert.resolved"
    ALERT_SNOOZE = "alert.snoozed"
    
    DASHBOARD_CREATE = "dashboard.created"
    DASHBOARD_UPDATE = "dashboard.updated"
    DASHBOARD_DELETE = "dashboard.deleted"
    DASHBOARD_SHARE = "dashboard.shared"
    
    MEMBER_LIST = "member.list" # Not in audit actions
    MEMBER_INVITE = "member.invited"
    MEMBER_REMOVE = "member.removed"
    MEMBER_ROLE_CHANGE = "member.role_changed"

# RBAC Matrix
# roles: owner | admin | editor | viewer
ROLE_PERMISSIONS: Dict[str, Set[ProjectPermission]] = {
    "viewer": {
        ProjectPermission.PROJECT_VIEW,
        ProjectPermission.MEMBER_LIST,
    },
    "editor": {
        ProjectPermission.PROJECT_VIEW,
        ProjectPermission.PROJECT_UPDATE,
        ProjectPermission.DEVICE_CREATE,
        ProjectPermission.DEVICE_UPDATE,
        ProjectPermission.DEVICE_DELETE,
        ProjectPermission.DEVICE_DISABLE,
        ProjectPermission.DEVICE_ENABLE,
        ProjectPermission.DEVICE_ROTATE_CREDS,
        ProjectPermission.RULE_CREATE,
        ProjectPermission.RULE_UPDATE,
        ProjectPermission.RULE_DELETE,
        ProjectPermission.RULE_ENABLE,
        ProjectPermission.RULE_DISABLE,
        ProjectPermission.ALERT_ACK,
        ProjectPermission.ALERT_RESOLVE,
        ProjectPermission.ALERT_SNOOZE,
        ProjectPermission.DASHBOARD_CREATE,
        ProjectPermission.DASHBOARD_UPDATE,
        ProjectPermission.DASHBOARD_DELETE,
        ProjectPermission.DASHBOARD_SHARE,
        ProjectPermission.MEMBER_LIST,
    },
    "admin": {
        p for p in ProjectPermission
    },
    "owner": {
        p for p in ProjectPermission
    }
}

class ProjectContext(BaseModel):
    org_role: Optional[str] = None
    project_role: Optional[str] = None

class PolicyEngine:
    @staticmethod
    def can(action: ProjectPermission, context: ProjectContext) -> bool:
        # Org Owner and Org Admin bypass all checks for projects within their org
        if context.org_role in ["owner", "admin"]:
            return True
        
        # If not an org admin, check project-specific role
        if not context.project_role:
            return False
            
        allowed_permissions = ROLE_PERMISSIONS.get(context.project_role, set())
        return action in allowed_permissions

    @staticmethod
    def assert_can(action: ProjectPermission, context: ProjectContext) -> None:
        if not PolicyEngine.can(action, context):
            from yp_shared.errors import AppError
            raise AppError(f"Action '{action.value}' is forbidden for your current role", "forbidden", 403)
