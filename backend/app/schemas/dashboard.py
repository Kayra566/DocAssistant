import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import Plan


class TrendPoint(BaseModel):
    date: str
    documents: int
    ai_jobs: int


class DistributionItem(BaseModel):
    key: str
    count: int


class DashboardTotals(BaseModel):
    documents: int
    ai_jobs: int
    share_links: int
    members: int


class DashboardQuota(BaseModel):
    documents_used: int
    documents_limit: int
    storage_bytes_used: int
    storage_bytes_limit: int
    ai_requests_used: int
    ai_requests_limit: int
    ai_tokens_used: int
    ai_tokens_limit: int


class DashboardStatsResponse(BaseModel):
    plan: Plan
    subscription_status: str
    totals: DashboardTotals
    quota: DashboardQuota
    usage_trend: list[TrendPoint]
    job_distribution: list[DistributionItem]
    document_status: list[DistributionItem]


class PlatformStatsResponse(BaseModel):
    users: int
    verified_users: int
    organizations: int
    documents: int
    ai_jobs: int
    share_links: int
    storage_bytes: int
    plan_distribution: list[DistributionItem]


class PlatformOrganizationResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    plan: Plan
    documents: int
    members: int
    created_at: datetime
