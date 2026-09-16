from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from src.core.config import settings

# Initialize async engine with connection string from settings
engine = create_async_engine(settings.DATABASE_URL, echo=False)

# Configure session maker
async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    # Dependency for FastAPI to provide a database session per request
    async with async_session_maker() as session:
        yield session
