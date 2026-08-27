import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import Plan


class PlanResponse(BaseModel):
    key: Plan
    name: str
    price_monthly: int
    currency: str
    documents: int
    storage_mb: int
    ai_requests: int
    ai_tokens: int
    features: list[str]


class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    plan: Plan
    status: str
    cancel_at_period_end: bool
    current_period_end: datetime | None


class CheckoutRequest(BaseModel):
    plan: Plan


class CheckoutResponse(BaseModel):
    session_id: str
    url: str


class PortalResponse(BaseModel):
    url: str


class BillingUsageResponse(BaseModel):
    plan: Plan
    status: str
    cancel_at_period_end: bool
    current_period_end: datetime | None
    documents_used: int
    documents_limit: int
    storage_bytes_used: int
    storage_bytes_limit: int
    ai_requests_used: int
    ai_requests_limit: int
    ai_tokens_used: int
    ai_tokens_limit: int


class WebhookAck(BaseModel):
    status: str
    event_id: str
