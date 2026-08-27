from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.cache import cache_key, get_cache
from app.ai.guards import moderate_output
from app.ai.json_output import parse_json_object
from app.ai.prompts import (
    COMPARE_INSTRUCTION,
    KEYPOINTS_INSTRUCTION,
    build_task_prompt,
    extract_instruction,
    quiz_instruction,
    summary_instruction,
    translate_instruction,
)
from app.ai.provider import SYSTEM_PROMPT, get_provider
from app.ai.tokens import estimate_tokens
from app.core.config import settings
from app.core.exceptions import NotFoundError, ValidationError
from app.models.ai import AIJob, AIJobStatus, AIJobType
from app.models.document import DocumentChunk
from app.services.ai_chat import load_ready_document
from app.services.quota import ensure_ai_quota

# Her görev için (çıktı biçimi, JSON anahtarları) tanımı.
JSON_SCHEMAS: dict[AIJobType, dict[str, Any]] = {
    AIJobType.KEYPOINTS: {"dates": [], "names": [], "numbers": [], "decisions": []},
    AIJobType.QUIZ: {"questions": []},
    AIJobType.EXTRACT: {"columns": [], "records": []},
    AIJobType.COMPARE: {"summary": "", "only_in_a": [], "only_in_b": [], "changed": []},
}


async def _document_context(
    db: AsyncSession, org_id: uuid.UUID, document_id: uuid.UUID, limit: int | None = None
) -> str:
    rows = (
        (
            await db.execute(
                select(DocumentChunk)
                .where(
                    DocumentChunk.organization_id == org_id,
                    DocumentChunk.document_id == document_id,
                )
                .order_by(DocumentChunk.chunk_index)
            )
        )
        .scalars()
        .all()
    )
    budget = limit or settings.AI_TASK_CONTEXT_CHARS
    blocks: list[str] = []
    used = 0
    for chunk in rows:
        block = f"[Sayfa {chunk.page}] {chunk.content}"
        if used + len(block) > budget:
            break
        blocks.append(block)
        used += len(block)
    return "\n---\n".join(blocks)


def _normalize_preset(params: dict) -> str:
    return str(params.get("preset") or "genel")


async def _build_prompt(db: AsyncSession, job: AIJob) -> str:
    """Job tipine göre LLM prompt'u üretir."""
    params = job.params or {}
    preset = _normalize_preset(params)
    context = await _document_context(db, job.organization_id, job.document_id)

    if job.type == AIJobType.SUMMARY:
        return build_task_prompt(
            task="summary",
            instruction=summary_instruction(str(params.get("level", "short"))),
            context=context,
            preset=preset,
        )
    if job.type == AIJobType.KEYPOINTS:
        return build_task_prompt(
            task="keypoints",
            instruction=KEYPOINTS_INSTRUCTION,
            context=context,
            preset=preset,
            output_format="json",
        )
    if job.type == AIJobType.QUIZ:
        return build_task_prompt(
            task="quiz",
            instruction=quiz_instruction(
                int(params.get("question_count", 5)),
                list(params.get("question_types") or ["multiple_choice"]),
            ),
            context=context,
            preset=preset,
            output_format="json",
        )
    if job.type == AIJobType.TRANSLATE:
        return build_task_prompt(
            task="translate",
            instruction=translate_instruction(
                str(params.get("target_language", "İngilizce")),
                params.get("source_language"),
            ),
            context=context,
            preset=preset,
        )
    if job.type == AIJobType.EXTRACT:
        return build_task_prompt(
            task="extract",
            instruction=extract_instruction(params.get("schema_hint")),
            context=context,
            preset=preset,
            output_format="json",
        )
    if job.type == AIJobType.COMPARE:
        other_id = uuid.UUID(str(params["other_document_id"]))
        half = settings.AI_TASK_CONTEXT_CHARS // 2
        left = await _document_context(db, job.organization_id, job.document_id, half)
        right = await _document_context(db, job.organization_id, other_id, half)
        return build_task_prompt(
            task="compare",
            instruction=COMPARE_INSTRUCTION,
            context=f"DOKÜMAN A:\n{left}\n\nDOKÜMAN B:\n{right}",
            preset=preset,
            output_format="json",
        )
    raise ValidationError(f"Desteklenmeyen görev tipi: {job.type}")


def _shape_result(job_type: AIJobType, raw: str) -> dict:
    schema = JSON_SCHEMAS.get(job_type)
    if schema is None:
        return {"text": raw}
    return parse_json_object(raw, keys=schema)


async def run_job(db: AsyncSession, job: AIJob) -> AIJob:
    """Görevi çalıştırır, sonucu job üzerine yazar ve commit eder."""
    job.status = AIJobStatus.RUNNING
    await db.flush()
    try:
        prompt = await _build_prompt(db, job)
        await ensure_ai_quota(db, job.organization_id, estimate_tokens(prompt))

        key = cache_key(
            job.type,
            str(job.document_id),
            json.dumps(job.params or {}, sort_keys=True, ensure_ascii=False),
        )
        cache = get_cache()
        cached = cache.get(key)
        if cached is not None:
            job.result = cached
            job.cache_hit = True
            job.tokens_used = 0
        else:
            raw = moderate_output(
                await get_provider().complete(system=SYSTEM_PROMPT, prompt=prompt)
            )
            job.result = _shape_result(job.type, raw)
            job.cache_hit = False
            job.tokens_used = estimate_tokens(prompt) + estimate_tokens(raw)
            cache.set(key, job.result, settings.AI_CACHE_TTL_SECONDS)
        job.status = AIJobStatus.DONE
        job.error = None
    except Exception as exc:
        job.status = AIJobStatus.FAILED
        job.error = str(exc)[:1000]
        await db.commit()
        raise
    await db.commit()
    await db.refresh(job)
    return job


async def _validate_params(
    db: AsyncSession, org_id: uuid.UUID, job_type: AIJobType, params: dict
) -> None:
    if job_type == AIJobType.QUIZ:
        count = int(params.get("question_count", 5))
        if not 1 <= count <= settings.AI_QUIZ_MAX_QUESTIONS:
            raise ValidationError(
                f"Soru sayısı 1-{settings.AI_QUIZ_MAX_QUESTIONS} arasında olmalı."
            )
    if job_type == AIJobType.COMPARE:
        other = params.get("other_document_id")
        if not other:
            raise ValidationError("Karşılaştırma için ikinci doküman gerekli.")
        await load_ready_document(db, org_id, uuid.UUID(str(other)))


async def create_job(
    db: AsyncSession,
    *,
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    document_id: uuid.UUID,
    job_type: AIJobType,
    params: dict,
) -> AIJob:
    """Görevi oluşturur; eager modda hemen çalıştırır, aksi halde kuyruğa atar."""
    doc = await load_ready_document(db, org_id, document_id)
    await _validate_params(db, org_id, job_type, params)
    await ensure_ai_quota(db, org_id)

    job = AIJob(
        organization_id=org_id,
        user_id=user_id,
        document_id=doc.id,
        type=job_type,
        status=AIJobStatus.PENDING,
        params=params,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    if settings.AI_JOBS_EAGER:
        return await run_job(db, job)

    from app.workers.ai_tasks import run_ai_job_task

    run_ai_job_task.delay(str(job.id))
    return job


async def list_jobs(
    db: AsyncSession,
    org_id: uuid.UUID,
    *,
    document_id: uuid.UUID | None = None,
    job_type: AIJobType | None = None,
    limit: int = 50,
) -> list[AIJob]:
    stmt = select(AIJob).where(AIJob.organization_id == org_id)
    if document_id:
        stmt = stmt.where(AIJob.document_id == document_id)
    if job_type:
        stmt = stmt.where(AIJob.type == job_type)
    stmt = stmt.order_by(AIJob.created_at.desc()).limit(limit)
    return list((await db.execute(stmt)).scalars().all())


async def get_job(db: AsyncSession, org_id: uuid.UUID, job_id: uuid.UUID) -> AIJob:
    job = (
        await db.execute(
            select(AIJob).where(AIJob.id == job_id, AIJob.organization_id == org_id)
        )
    ).scalar_one_or_none()
    if not job:
        raise NotFoundError("AI görevi bulunamadı.")
    return job


async def delete_job(db: AsyncSession, org_id: uuid.UUID, job_id: uuid.UUID) -> None:
    job = await get_job(db, org_id, job_id)
    await db.delete(job)
    await db.commit()
