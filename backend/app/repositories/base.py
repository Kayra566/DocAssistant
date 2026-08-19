import uuid
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

ModelT = TypeVar("ModelT", bound=Base)


class TenantScopedRepository(Generic[ModelT]):
    """Her sorguya otomatik `organization_id == tenant_id` filtresi ekler.

    Tenant izolasyonunun tek noktadan garanti altına alındığı katman.
    Model'in `organization_id` kolonu olmalıdır.
    """

    model: type[ModelT]

    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _scoped(self):
        return select(self.model).where(
            self.model.organization_id == self.tenant_id  # type: ignore[attr-defined]
        )

    async def get(self, obj_id: uuid.UUID) -> ModelT | None:
        stmt = self._scoped().where(self.model.id == obj_id)  # type: ignore[attr-defined]
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def list(self) -> list[ModelT]:
        return list((await self.db.execute(self._scoped())).scalars().all())

    async def add(self, obj: ModelT) -> ModelT:
        # Tenant kimliğini repository zorlar; çağıran override edemez.
        obj.organization_id = self.tenant_id  # type: ignore[attr-defined]
        self.db.add(obj)
        await self.db.flush()
        return obj

    async def delete(self, obj: ModelT) -> None:
        await self.db.delete(obj)
        await self.db.flush()
