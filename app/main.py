from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
from app.core.config import settings
from app.models.base import engine, Base
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

import app.models.user_model

from app.api.controllers import auth_routes

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
    
    yield # runs application
    
    await engine.dispose()

# init the app with the lifespan event
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware, 
    allow_origins = settings.ORIGINS_API,
    allow_methods=["*"],
    allow_headers=["*"]
)



app.include_router(auth_routes.router, prefix=settings.API_V1_STR, tags=["Authentication"])



@app.get("/")
async def root():
    return {"message": "Welcome to the API", "project": settings.PROJECT_NAME}