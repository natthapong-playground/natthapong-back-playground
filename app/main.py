from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
from app.core.config import settings
from app.core.redis_client import get_redis_client, close_redis_client
from app.core.middleware import AuditLogMiddleware
from app.models.base import engine, Base
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

import app.models.user_model
import app.models.audit_log_model

from app.api.controllers import auth_routes, user_routes, audit_routes, countries_routes, clock_routes



# class SecurityHeadersMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request, call_next):
#         response: Response = await call_next(request)
#         response.headers['X-Content-Type-Options'] = 'nosniff'
#         response.headers['X-Frame-Options'] = 'DENY'
#         response.headers['Content-Security-Policy'] = "default-src 'self'; img-src 'self' data:; script-src 'self'; style-src 'self' 'unsafe-inline'"
#         response.headers['Strict-Transport-Security'] = 'max-age=63072000; includeSubDomains; preload'
#         return response

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

# app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(AuditLogMiddleware)

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