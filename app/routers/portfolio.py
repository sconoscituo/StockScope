from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.portfolio import Portfolio, TradeType
from app.models.user import User
from app.utils.auth import get_current_active_user

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


class PortfolioCreate(BaseModel):
    ticker: str
    name: Optional[str] = None
    trade_type: TradeType
    quantity: float
    price: float
    target_price: Optional[float] = None
    memo: Optional[str] = None
    traded_at: Optional[datetime] = None


class PortfolioResponse(BaseModel):
    id: int
    ticker: str
    name: Optional[str]
    trade_type: TradeType
    quantity: float
    price: float
    target_price: Optional[float]
    memo: Optional[str]
    traded_at: datetime
    total_value: float

    class Config:
        from_attributes = True


@router.post("/", summary="매수/매도 기록 추가", status_code=status.HTTP_201_CREATED)
async def add_trade(
    body: PortfolioCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """포트폴리오에 매수 또는 매도 기록을 추가합니다."""
    entry = Portfolio(
        user_id=current_user.id,
        ticker=body.ticker.upper(),
        name=body.name,
        trade_type=body.trade_type,
        quantity=body.quantity,
        price=body.price,
        target_price=body.target_price,
        memo=body.memo,
        traded_at=body.traded_at or datetime.utcnow(),
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return {
        "message": "거래 기록이 추가되었습니다.",
        "id": entry.id,
        "ticker": entry.ticker,
        "trade_type": entry.trade_type,
        "quantity": entry.quantity,
        "price": entry.price,
        "total_value": entry.quantity * entry.price,
    }


@router.get("/", summary="내 포트폴리오 조회")
async def get_portfolio(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """현재 로그인한 사용자의 모든 거래 기록을 반환합니다."""
    result = await db.execute(
        select(Portfolio)
        .where(Portfolio.user_id == current_user.id)
        .order_by(Portfolio.traded_at.desc())
    )
    trades = result.scalars().all()

    summary: dict = {}
    for t in trades:
        ticker = t.ticker
        if ticker not in summary:
            summary[ticker] = {"ticker": ticker, "name": t.name, "quantity": 0.0, "avg_price": 0.0, "total_cost": 0.0}
        if t.trade_type == TradeType.BUY:
            prev_total = summary[ticker]["avg_price"] * summary[ticker]["quantity"]
            summary[ticker]["quantity"] += t.quantity
            summary[ticker]["total_cost"] = prev_total + t.quantity * t.price
            if summary[ticker]["quantity"] > 0:
                summary[ticker]["avg_price"] = summary[ticker]["total_cost"] / summary[ticker]["quantity"]
        else:
            summary[ticker]["quantity"] -= t.quantity

    return {
        "total_trades": len(trades),
        "holdings": [v for v in summary.values() if v["quantity"] > 0],
        "trades": [
            {
                "id": t.id,
                "ticker": t.ticker,
                "trade_type": t.trade_type,
                "quantity": t.quantity,
                "price": t.price,
                "total_value": t.quantity * t.price,
                "target_price": t.target_price,
                "memo": t.memo,
                "traded_at": t.traded_at.isoformat(),
            }
            for t in trades
        ],
    }


@router.delete("/{trade_id}", summary="거래 기록 삭제")
async def delete_trade(
    trade_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Portfolio).where(Portfolio.id == trade_id, Portfolio.user_id == current_user.id)
    )
    trade = result.scalar_one_or_none()
    if not trade:
        raise HTTPException(status_code=404, detail="거래 기록을 찾을 수 없습니다.")
    await db.delete(trade)
    await db.commit()
    return {"message": "거래 기록이 삭제되었습니다."}
