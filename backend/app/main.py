"""CropGuard Network — FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.postgres import engine
from app.routers import auth, diagnosis, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle — disposes the async engine on exit."""
    yield
    await engine.dispose()


app = FastAPI(
    title="CropGuard Network",
    description="Crop disease detection and regional outbreak advisory for Chh. Sambhajinagar district",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(diagnosis.router, prefix="/api/diagnosis", tags=["Diagnosis"])
