from fastapi import APIRouter, Depends
from app.services.analytics_service import AnalyticsService
from app.middleware.role_middleware import require_admin

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/overview", dependencies=[Depends(require_admin)])
async def get_analytics_overview():
    data = await AnalyticsService.get_overview()
    return {"success": True, "message": "Analytics retrieved", "data": data}

@router.get("/leaderboard")
async def get_leaderboard():
    data = await AnalyticsService.get_leaderboard()
    return {"success": True, "message": "Leaderboard retrieved", "data": data}
