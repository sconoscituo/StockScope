from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.analysis import MarketAnalysis
from app.schemas.stock import MarketAnalysisResponse
from app.utils.auth import get_current_active_user
import json

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get("", response_model=List[MarketAnalysisResponse])
async def list_analyses(
    limit: int = 5,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """최근 시장 분석 목록을 반환합니다."""
    result = await db.execute(
        select(MarketAnalysis)
        .order_by(desc(MarketAnalysis.created_at))
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/latest", response_model=MarketAnalysisResponse)
async def get_latest_analysis(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """가장 최근 시장 분석을 반환합니다."""
    result = await db.execute(
        select(MarketAnalysis).order_by(desc(MarketAnalysis.created_at)).limit(1)
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="아직 분석 데이터가 없습니다.")
    return analysis


@router.post("/run", response_model=MarketAnalysisResponse, status_code=201)
async def run_analysis(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """시장 분석을 즉시 실행합니다."""
    from app.services.news_analyzer import run_news_analysis

    result_data = run_news_analysis()

    key_events = result_data.get("key_events", [])
    key_events_json = json.dumps(key_events, ensure_ascii=False)

    analysis = MarketAnalysis(
        summary=result_data.get("summary", ""),
        sentiment=result_data.get("sentiment", "NEUTRAL"),
        sentiment_score=result_data.get("sentiment_score"),
        key_events=key_events_json,
        source_count=result_data.get("source_count", 0),
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)
    return analysis
