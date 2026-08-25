import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.core.storage as storage_module
from app.core.database import Base, get_db
from app.core.storage import LocalStorage
from app.main import app

# Tüm testler için paylaşılan in-memory SQLite (StaticPool tek bağlantıyı paylaşır).
test_engine = create_async_engine(
    "sqlite+aiosqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(autouse=True)
async def _setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
def _isolated_storage(tmp_path):
    """Her test için ayrı bir yerel depolama dizini kullan."""
    storage_module._storage = LocalStorage(str(tmp_path / "storage"))
    yield
    storage_module._storage = None


@pytest.fixture
async def client():
    async def _override_get_db():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


STRONG_PASSWORD = "Tr0ub4dour&3xample!"


async def register_user(
    client: AsyncClient, email: str, password: str = STRONG_PASSWORD, **kwargs
):
    return await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, **kwargs},
    )


async def login_user(client: AsyncClient, email: str, password: str = STRONG_PASSWORD):
    return await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )


def auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


async def setup_org(client: AsyncClient, email: str) -> tuple[str, str]:
    """Kullanıcı oluşturur, giriş yapar; (access_token, org_id) döndürür."""
    reg = (await register_user(client, email)).json()
    access = (await login_user(client, email)).json()["access_token"]
    return access, reg["organization_id"]


