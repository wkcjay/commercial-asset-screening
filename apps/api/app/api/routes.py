from datetime import UTC, datetime

from fastapi import APIRouter, Request
from sqlalchemy.engine import Engine

from app.api.errors import AppError
from app.db import repositories
from app.models.api import (
    ApiEnvelope,
    ApiEnvelopeMeta,
    AssessmentData,
    CommercialAssetAssessmentData,
    GenerateMemoRequest,
    HealthResponse,
    ListCommercialAssetsData,
    ListSitesData,
    MemoData,
)
from app.services.commercial import (
    CommercialAssetNotFoundError,
    assess_commercial_asset,
    list_commercial_asset_summaries,
)
from app.services.assessment import NotFoundError, assess_site, list_site_summaries
from app.services.memo import generate_commercial_memo, generate_memo


router = APIRouter()


def _engine(request: Request) -> Engine:
    return request.app.state.engine


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _envelope(request: Request, data, data_version: str | None = None, cache_meta=None, warnings: list[str] | None = None):
    return ApiEnvelope(
        data=data,
        meta=ApiEnvelopeMeta(
            requestId=_request_id(request),
            generatedAt=_now(),
            dataVersion=data_version,
            cache=cache_meta,
            warnings=warnings or [],
        ),
    )


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    settings = request.app.state.settings
    return HealthResponse(
        ok=True,
        version="local",
        dataMode=settings.data_mode,
        aiConfigured=bool(settings.enable_ai_memo and settings.ai_api_key and settings.ai_model),
    )


@router.get("/sites", response_model=ApiEnvelope[ListSitesData])
def sites(request: Request):
    engine = _engine(request)
    data_version = repositories.get_current_data_version(engine)
    return _envelope(
        request,
        ListSitesData(sites=list_site_summaries(engine)),
        data_version=data_version,
    )


@router.get("/commercial-assets", response_model=ApiEnvelope[ListCommercialAssetsData])
def commercial_assets(request: Request):
    engine = _engine(request)
    data_version = repositories.get_current_data_version(engine)
    return _envelope(
        request,
        ListCommercialAssetsData(assets=list_commercial_asset_summaries(engine)),
        data_version=data_version,
    )


@router.get("/sites/{site_id}/assessment", response_model=ApiEnvelope[AssessmentData])
def assessment(request: Request, site_id: str):
    try:
        result = assess_site(_engine(request), site_id)
    except NotFoundError as exc:
        raise AppError("not_found", str(exc), 404) from exc
    return _envelope(
        request,
        AssessmentData(assessment=result.assessment),
        data_version=result.data_version,
        cache_meta=result.cache_meta,
        warnings=result.warnings,
    )


@router.get("/commercial-assets/{asset_id}/assessment", response_model=ApiEnvelope[CommercialAssetAssessmentData])
def commercial_assessment(request: Request, asset_id: str):
    try:
        result = assess_commercial_asset(_engine(request), asset_id)
    except CommercialAssetNotFoundError as exc:
        raise AppError("not_found", str(exc), 404) from exc
    return _envelope(
        request,
        CommercialAssetAssessmentData(assessment=result.assessment),
        data_version=result.data_version,
        cache_meta=result.cache_meta,
        warnings=result.warnings,
    )


@router.post("/sites/{site_id}/memo", response_model=ApiEnvelope[MemoData])
def memo(request: Request, site_id: str, payload: GenerateMemoRequest | None = None):
    try:
        assessment_result = assess_site(_engine(request), site_id)
    except NotFoundError as exc:
        raise AppError("not_found", str(exc), 404) from exc
    tone = payload.tone if payload else "investment-committee"
    memo_result = generate_memo(_engine(request), assessment_result.assessment, tone, request.app.state.settings)
    return _envelope(
        request,
        memo_result.data,
        data_version=assessment_result.data_version,
        cache_meta=memo_result.cache_meta,
        warnings=assessment_result.warnings + memo_result.warnings,
    )


@router.post("/commercial-assets/{asset_id}/memo", response_model=ApiEnvelope[MemoData])
def commercial_memo(request: Request, asset_id: str, payload: GenerateMemoRequest | None = None):
    try:
        assessment_result = assess_commercial_asset(_engine(request), asset_id)
    except CommercialAssetNotFoundError as exc:
        raise AppError("not_found", str(exc), 404) from exc
    tone = payload.tone if payload else "investment-committee"
    memo_result = generate_commercial_memo(_engine(request), assessment_result.assessment, tone, request.app.state.settings)
    return _envelope(
        request,
        memo_result.data,
        data_version=assessment_result.data_version,
        cache_meta=memo_result.cache_meta,
        warnings=assessment_result.warnings + memo_result.warnings,
    )
