from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from yp_shared.health import router as health_router
from yp_shared.db import create_db_session_factory
from yp_shared.redis import create_redis_client
from yp_shared.nats import connect_nats
from yp_api.settings import settings
from yp_shared.errors import AppError
from fastapi.responses import JSONResponse
from yp_api.interfaces.http.v1.auth import router as v1_auth_router
from yp_api.interfaces.http.v1.organizations import router as v1_organizations_router
from yp_api.interfaces.http.v1.projects import router as v1_projects_router

def create_app() -> FastAPI:
    app = FastAPI(title=settings.PROJECT_NAME)
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize dependencies
    if settings.POSTGRES_DSN:
        app.state.db_session_maker = create_db_session_factory(str(settings.POSTGRES_DSN))
    
    if settings.REDIS_URL:
        app.state.redis = create_redis_client(settings.REDIS_URL)
    else:
        app.state.redis = None

    @app.on_event("startup")
    async def startup():
        app.state.nats_client = await connect_nats(settings.NATS_URL)
        app.state.js = app.state.nats_client.jetstream()

    app.include_router(health_router)
    app.include_router(v1_auth_router, prefix="/v1")
    app.include_router(v1_organizations_router, prefix="/v1/organizations")
    app.include_router(v1_projects_router, prefix="/v1/projects")
    
    @app.on_event("shutdown")
    async def shutdown():
        if hasattr(app.state, "redis") and app.state.redis:
            await app.state.redis.close()
        if hasattr(app.state, "nats_client") and app.state.nats_client:
            await app.state.nats_client.close()
            
    @app.exception_handler(AppError)
    async def app_error_handler(request, exc: AppError):
        # Default to 400 if no status_code is set
        status_code = getattr(exc, "status_code", 400)
        return JSONResponse(
            status_code=status_code,
            content={"error": {"code": getattr(exc, "code", "internal_error"), "message": str(exc)}}
        )
            
    return app
