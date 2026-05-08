from fastapi import APIRouter
from .sign_up import router as sign_up_router
from .verify_email import router as verify_email_router
from .login import router as login_router
from .refresh import router as refresh_router
from .logout import router as logout_router
from .password_reset import router as password_reset_router
from .magic_link import router as magic_link_router
from .sessions import router as sessions_router

router = APIRouter(prefix="/auth", tags=["auth"])
router.include_router(sign_up_router)
router.include_router(verify_email_router)
router.include_router(login_router)
router.include_router(refresh_router)
router.include_router(logout_router)
router.include_router(password_reset_router)
router.include_router(magic_link_router)
router.include_router(sessions_router)
