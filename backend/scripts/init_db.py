"""E2E/smoke ortamı için şemayı doğrudan modellerden oluşturur.

Migration zinciri prod içindir; burada hızlı ve bağımsız bir şema kurulumu yeterlidir.
"""

import asyncio

import app.models  # noqa: F401  — tablo tanımlarının kaydolması için
from app.core.database import Base, engine


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Schema created.")


if __name__ == "__main__":
    asyncio.run(main())
