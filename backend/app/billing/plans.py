from __future__ import annotations

from dataclasses import dataclass, field

from app.core.config import settings
from app.models.enums import Plan


@dataclass(frozen=True)
class PlanSpec:
    key: Plan
    name: str
    price_monthly: int
    currency: str
    documents: int
    storage_mb: int
    ai_requests: int
    ai_tokens: int
    features: list[str] = field(default_factory=list)


def plan_catalog() -> dict[Plan, PlanSpec]:
    return {
        Plan.FREE: PlanSpec(
            key=Plan.FREE,
            name="Free",
            price_monthly=0,
            currency=settings.BILLING_CURRENCY,
            documents=settings.QUOTA_FREE_DOCUMENTS,
            storage_mb=settings.QUOTA_FREE_STORAGE_MB,
            ai_requests=settings.QUOTA_FREE_AI_REQUESTS,
            ai_tokens=settings.QUOTA_FREE_AI_TOKENS,
            features=["Doküman sohbeti", "Temel AI araçları"],
        ),
        Plan.PRO: PlanSpec(
            key=Plan.PRO,
            name="Pro",
            price_monthly=settings.PRICE_PRO_MONTHLY,
            currency=settings.BILLING_CURRENCY,
            documents=settings.QUOTA_PRO_DOCUMENTS,
            storage_mb=settings.QUOTA_PRO_STORAGE_MB,
            ai_requests=settings.QUOTA_PRO_AI_REQUESTS,
            ai_tokens=settings.QUOTA_PRO_AI_TOKENS,
            features=["Tüm AI araçları", "2FA (TOTP)", "Öncelikli işleme"],
        ),
        Plan.BUSINESS: PlanSpec(
            key=Plan.BUSINESS,
            name="Business",
            price_monthly=settings.PRICE_BUSINESS_MONTHLY,
            currency=settings.BILLING_CURRENCY,
            documents=settings.QUOTA_BUSINESS_DOCUMENTS,
            storage_mb=settings.QUOTA_BUSINESS_STORAGE_MB,
            ai_requests=settings.QUOTA_BUSINESS_AI_REQUESTS,
            ai_tokens=settings.QUOTA_BUSINESS_AI_TOKENS,
            features=["Sınırsız doküman", "Öncelikli destek", "Ekip yönetimi"],
        ),
    }


def get_plan(plan: Plan) -> PlanSpec:
    return plan_catalog()[plan]


def price_id(plan: Plan) -> str:
    return {
        Plan.PRO: settings.STRIPE_PRICE_PRO,
        Plan.BUSINESS: settings.STRIPE_PRICE_BUSINESS,
    }[plan]


def plan_for_price_id(value: str) -> Plan | None:
    for plan in (Plan.PRO, Plan.BUSINESS):
        if price_id(plan) == value:
            return plan
    return None
