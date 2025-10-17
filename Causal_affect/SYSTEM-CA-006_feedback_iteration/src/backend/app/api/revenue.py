"""Revenue API router - placeholder."""
from fastapi import APIRouter, HTTPException, status
router = APIRouter(prefix="/revenue", tags=["revenue"])

@router.get("/summary")
async def get_revenue_summary():
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")
