"""Health and status endpoints for the RAG API."""

from fastapi import APIRouter, HTTPException
from src.api.models import SystemStatusResponse, HealthCheckResponse

router = APIRouter(tags=["Health"])

# These will be injected by the app
_status_checker = None


def set_status_checker(checker_func):
    """Set the status checker function for use by the endpoints."""
    global _status_checker
    _status_checker = checker_func


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    responses={
        200: {"description": "API is healthy"},
    },
)
async def health_check() -> HealthCheckResponse:
    """
    Simple health check endpoint.
    """
    return HealthCheckResponse(
        status="healthy",
        version="1.0.0",
    )


@router.get(
    "/status",
    response_model=SystemStatusResponse,
    responses={
        200: {"description": "Status information"},
        503: {"description": "System not ready"},
    },
)
async def system_status() -> SystemStatusResponse:
    """
    Get detailed system status including index statistics.
    """
    if not _status_checker:
        raise HTTPException(
            status_code=503,
            detail="Status checker not initialized",
        )

    try:
        status_info = _status_checker()
        return SystemStatusResponse(**status_info)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve status: {exc}",
        )
