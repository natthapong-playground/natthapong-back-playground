from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.models.base import engine, Base

import app.models.user_model 

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

@app.get("/")
async def root():
    return {"message": "Welcome to the API", "project": settings.PROJECT_NAME}