import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.prompts import PROMPT_PRESETS, SUMMARY_LEVELS
from app.api.deps import require_role
from app.core.database import get_db
from app.models.ai import AIJobType
from app.models.enums import Role
from app.models.user import User
from app.schemas.ai_features import (
    AIJobResponse,
    CompareRequest,
    ExtractRequest,
    KeyPointsRequest,
    PresetInfo,
    PromptPresetsResponse,
    QuizRequest,
    SummaryRequest,
    TranslateRequest,
)
from app.services import ai_features

router = APIRouter(prefix="/ai", tags=["ai-tools"])

require_viewer = require_role(Role.VIEWER)
require_member = require_role(Role.MEMBER)


async def _create(
    db: AsyncSession,
    org_id: uuid.UUID,
    user: User,
    job_type: AIJobType,
    document_id: uuid.UUID,
    params: dict,
) -> AIJobResponse:
    job = await ai_features.create_job(
        db,
        org_id=org_id,
        user_id=user.id,
        document_id=document_id,
        job_type=job_type,
        params=params,
    )
    return AIJobResponse.model_validate(job)


@router.get("/prompt-presets", response_model=PromptPresetsResponse)
async def prompt_presets() -> PromptPresetsResponse:
    return PromptPresetsResponse(
        presets=[PresetInfo(key=k, description=v) for k, v in PROMPT_PRESETS.items()],
        summary_levels=[
            PresetInfo(key=k, description=v) for k, v in SUMMARY_LEVELS.items()
        ],
    )


@router.post("/{org_id}/summary", response_model=AIJobResponse)
async def summary(
    org_id: uuid.UUID,
    payload: SummaryRequest,
    user: User = Depends(require_member),
    db: AsyncSession = Depends(get_db),
):
    return await _create(
        db,
        org_id,
        user,
        AIJobType.SUMMARY,
        payload.document_id,
        {"level": payload.level, "preset": payload.preset},
    )


@router.post("/{org_id}/keypoints", response_model=AIJobResponse)
async def keypoints(
    org_id: uuid.UUID,
    payload: KeyPointsRequest,
    user: User = Depends(require_member),
    db: AsyncSession = Depends(get_db),
):
    return await _create(
        db,
        org_id,
        user,
        AIJobType.KEYPOINTS,
        payload.document_id,
        {"preset": payload.preset},
    )


@router.post("/{org_id}/quiz", response_model=AIJobResponse)
async def quiz(
    org_id: uuid.UUID,
    payload: QuizRequest,
    user: User = Depends(require_member),
    db: AsyncSession = Depends(get_db),
):
    return await _create(
        db,
        org_id,
        user,
        AIJobType.QUIZ,
        payload.document_id,
        {
            "preset": payload.preset,
            "question_count": payload.question_count,
            "question_types": payload.question_types,
        },
    )


@router.post("/{org_id}/translate", response_model=AIJobResponse)
async def translate(
    org_id: uuid.UUID,
    payload: TranslateRequest,
    user: User = Depends(require_member),
    db: AsyncSession = Depends(get_db),
):
    return await _create(
        db,
        org_id,
        user,
        AIJobType.TRANSLATE,
        payload.document_id,
        {
            "preset": payload.preset,
            "target_language": payload.target_language,
            "source_language": payload.source_language,
        },
    )


@router.post("/{org_id}/extract", response_model=AIJobResponse)
async def extract(
    org_id: uuid.UUID,
    payload: ExtractRequest,
    user: User = Depends(require_member),
    db: AsyncSession = Depends(get_db),
):
    return await _create(
        db,
        org_id,
        user,
        AIJobType.EXTRACT,
        payload.document_id,
        {"preset": payload.preset, "schema_hint": payload.schema_hint},
    )


@router.post("/{org_id}/compare", response_model=AIJobResponse)
async def compare(
    org_id: uuid.UUID,
    payload: CompareRequest,
    user: User = Depends(require_member),
    db: AsyncSession = Depends(get_db),
):
    return await _create(
        db,
        org_id,
        user,
        AIJobType.COMPARE,
        payload.document_id,
        {
            "preset": payload.preset,
            "other_document_id": str(payload.other_document_id),
        },
    )


@router.get("/{org_id}/jobs", response_model=list[AIJobResponse])
async def list_jobs(
    org_id: uuid.UUID,
    document_id: uuid.UUID | None = Query(default=None),
    type: AIJobType | None = Query(default=None),
    user: User = Depends(require_viewer),
    db: AsyncSession = Depends(get_db),
):
    jobs = await ai_features.list_jobs(
        db, org_id, document_id=document_id, job_type=type
    )
    return [AIJobResponse.model_validate(j) for j in jobs]


@router.get("/{org_id}/jobs/{job_id}", response_model=AIJobResponse)
async def get_job(
    org_id: uuid.UUID,
    job_id: uuid.UUID,
    user: User = Depends(require_viewer),
    db: AsyncSession = Depends(get_db),
):
    return AIJobResponse.model_validate(await ai_features.get_job(db, org_id, job_id))


@router.delete("/{org_id}/jobs/{job_id}", status_code=204)
async def delete_job(
    org_id: uuid.UUID,
    job_id: uuid.UUID,
    user: User = Depends(require_member),
    db: AsyncSession = Depends(get_db),
):
    await ai_features.delete_job(db, org_id, job_id)
