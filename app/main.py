from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from app.core.config import settings
from app.core.redis_client import get_redis_client, close_redis_client
from app.core.middleware import AuditLogMiddleware, SecurityHeadersMiddleware
from app.models.base import engine, Base
from fastapi.middleware.cors import CORSMiddleware

import app.models.user_model
import app.models.audit_log_model

from app.api.controllers import auth_routes, user_routes, audit_routes, countries_routes, clock_routes



@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Connecting to the database and creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully!")
    
    await get_redis_client().ping()
    yield # runs application
    
    await close_redis_client()
    await engine.dispose()

# init the app with the lifespan event
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

app.add_middleware(AuditLogMiddleware)

app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins = settings.ORIGINS_API,
    allow_methods=["*"],
    allow_headers=["*"]
)



app.include_router(auth_routes.router, prefix=settings.API_V1_STR, tags=["Authentication"])
app.include_router(user_routes.router, prefix=f"{settings.API_V1_STR}/users", tags=["UsersRoutes"])
app.include_router(audit_routes.router, prefix=settings.API_V1_STR, tags=["AuditLogs"])
app.include_router(countries_routes.router, prefix=settings.API_V1_STR, tags=["Countries"])
app.include_router(clock_routes.router, prefix=settings.API_V1_STR, tags=["Clock"])



@app.get("/")
async def root():
    return {"message": "Welcome to the API", "project": settings.PROJECT_NAME}


@app.get("/health")
async def health():
    # Readiness probe for Docker/monitoring: verifies DB + Redis are reachable.
    db_ok = True
    redis_ok = True
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        db_ok = False
    try:
        await get_redis_client().ping()
    except Exception:
        redis_ok = False

    healthy = db_ok and redis_ok
    return JSONResponse(
        status_code=200 if healthy else 503,
        content={
            "status": "ok" if healthy else "degraded",
            "database": db_ok,
            "redis": redis_ok,
        },
    )