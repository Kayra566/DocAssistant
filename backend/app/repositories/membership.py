import uuid

from app.models.organization import Membership
from app.repositories.base import TenantScopedRepository


class MembershipRepository(TenantScopedRepository[Membership]):
    model = Membership

    async def get_by_user(self, user_id: uuid.UUID) -> Membership | None:
        for m in await self.list():
            if m.user_id == user_id:
                return m
        return None
