"""Iteration API endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.get("/")
async def list_iterations() -> dict[str, Any]:
    """List all iterations."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint not implemented yet"
    )


@router.post("/")
async def create_iteration() -> dict[str, Any]:
    """Create new iteration."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint not implemented yet"
    )


@router.get("/{iteration_id}")
async def get_iteration(iteration_id: int) -> dict[str, Any]:
    """Get iteration details."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint not implemented yet"
    )


@router.put("/{iteration_id}")
async def update_iteration(iteration_id: int) -> dict[str, Any]:
    """Update iteration."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint not implemented yet"
    )


@router.delete("/{iteration_id}")
async def delete_iteration(iteration_id: int) -> dict[str, Any]:
    """Delete iteration."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint not implemented yet"
    )


@router.get("/{iteration_id}/features")
async def get_iteration_features(iteration_id: int) -> dict[str, Any]:
    """Get features assigned to iteration."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint not implemented yet"
    )
