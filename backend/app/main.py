from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.database import init_db, close_db
from app.api.routes import health, agents
from app.models.agent import Agent  # Ensure model is registered


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings = get_settings()

    # Refuse demo mode in production
    if settings.is_production and settings.demo_mode:
        raise RuntimeError("Demo mode is not allowed in production. Set DEMO_MODE=false.")

    # Create data directory
    import os
    data_dir = "./data"
    os.makedirs(data_dir, exist_ok=True)
    workspace_dir = os.path.join(data_dir, "workspaces")
    os.makedirs(workspace_dir, exist_ok=True)

    # Initialize database
    await init_db()

    yield

    # Shutdown
    await close_db()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="A smarter, self-hosted AI assistant — multi-user, multi-agent",
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    @app.exception_handler(ValueError)
    async def value_error_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(PermissionError)
    async def permission_error_handler(request, exc):
        return JSONResponse(status_code=403, content={"detail": str(exc)})

    # Include routers
    app.include_router(health.router)
    app.include_router(agents.router)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)