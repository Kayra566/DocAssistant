import enum


class Role(enum.StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class Plan(enum.StrEnum):
    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"


# Rol hiyerarşisi (büyük sayı = daha yetkili). RBAC karşılaştırmaları için.
ROLE_LEVEL: dict[Role, int] = {
    Role.VIEWER: 1,
    Role.MEMBER: 2,
    Role.ADMIN: 3,
    Role.OWNER: 4,
}
