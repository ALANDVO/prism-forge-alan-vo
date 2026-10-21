import sys
import os
import tempfile
import asyncio
from collections.abc import AsyncGenerator
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# Set test environment before importing app
os.environ["ENVIRONMENT"] = "development"
os.environ["DEBUG"] = "true"
os.environ["DEMO_MODE"] = "true"

from app.core.config import get_settings
from app.core.database import Base
from app.main import create_app
from app.models.agent import Agent


class TestBase(DeclarativeBase):
    pass


@pytest.fixture(scope="session")
def test_db_path() -> Path:
    """Create a temporary database file for the test session."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    yield db_path
    # Cleanup
    if db_path.exists():
        db_path.unlink()
    # Also cleanup -wal and -shm files
    for suffix in ["-wal", "-shm"]:
        wal_path = Path(str(db_path) + suffix)
        if wal_path.exists():
            wal_path.unlink()


@pytest.fixture(scope="session")
def test_engine(test_db_path):
    """Create test database engine."""
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{test_db_path}",
        echo=False,
        future=True,
    )
    yield engine
    # Cleanup handled by test_db_path fixture


@pytest.fixture(scope="session", autouse=True)
async def init_test_db(test_engine):
    """Initialize test database schema."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await test_engine.dispose()


async def init_db_for_engine(engine):
    """Create all tables for the given engine."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a database session for a test."""
    async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest.fixture
def app(test_engine):
    """Create FastAPI app with test database."""
    # Override database URL
    original_get_settings = get_settings

    def override_get_settings():
        settings = original_get_settings()
        settings.database_url = f"sqlite+aiosqlite:///{test_db_path}"
        settings.demo_mode = True
        settings.environment = "development"
        return settings

    import app.core.config as config_module
    config_module.get_settings = override_get_settings

    # Also override in database module
    import app.core.database as db_module
    original_engine = db_module.engine
    original_session = db_module.AsyncSessionLocal
    db_module.engine = test_engine
    db_module.AsyncSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    # Ensure tables are created for this engine
    asyncio.run(init_db_for_engine(test_engine))

    app = create_app()

    yield app

    # Restore
    config_module.get_settings = original_get_settings
    db_module.engine = original_engine
    db_module.AsyncSessionLocal = original_session


@pytest.fixture
def client(app) -> AsyncClient:
    """Create async test client."""
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.fixture
async def demo_user():
    """Demo user for testing."""
    from app.core.security import DemoUser
    return DemoUser()