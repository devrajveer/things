from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

def create_db_session_factory(dsn: str) -> async_sessionmaker[AsyncSession]:
    """Create an async SQLAlchemy session factory."""
    engine = create_async_engine(dsn, echo=False)
    return async_sessionmaker(engine, expire_on_commit=False)

async def check_db_health(session_factory: async_sessionmaker[AsyncSession]) -> bool:
    from sqlalchemy import text
    try:
        async with session_factory() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
