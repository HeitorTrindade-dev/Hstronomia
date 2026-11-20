import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import Base, async_session_factory, get_db


def test_base_metadata_exists():
    assert Base.metadata is not None


@pytest.mark.asyncio
async def test_get_db_yields_session():
    async for session in get_db():
        assert isinstance(session, AsyncSession)
        assert session.is_active
        break
