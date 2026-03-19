from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List

from app.database import get_db
from app.models.user import User, PlanType
from app.models.stock import WatchStock
from app.models.signal import TradeSignal
from app.schemas.stock import StockAdd, StockResponse, SignalResponse
from app.utils.auth import get_current_active_user
from app.config import settings

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


@router.post("", response_model=StockResponse, status_code=201)
async def add_stock(
    stock_in: StockAdd,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    # 구독 플랜 확인
    result = await db.execute(
        select(WatchStock).where(WatchStock.user_id == current_user.id)
    )
    existing_stocks = result.scalars().all()

    if (
        current_user.plan == PlanType.FREE
        and len(existing_stocks) >= settings.FREE_PLAN_STOCK_LIMIT
    ):
        raise HTTPException(
            status_code=403,
            detail=f"무료 플랜은 최대 {settings.FREE_PLAN_STOCK_LIMIT}개 종목만 등록 가능합니다. 프리미엄으로 업그레이드하세요.",
        )

    # 중복 확인
    dup = await db.execute(
        select(WatchStock).where(
            WatchStock.user_id == current_user.id,
            WatchStock.ticker == stock_in.ticker.upper(),
        )
    )
    if dup.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="이미 등록된 종목입니다.")

    stock = WatchStock(
        user_id=current_user.id,
        ticker=stock_in.ticker.upper(),
        name=stock_in.name,
        market=stock_in.market,
    )
    db.add(stock)
    await db.commit()
    await db.refresh(stock)
    return stock


@router.get("", response_model=List[StockResponse])
async def list_stocks(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WatchStock).where(WatchStock.user_id == current_user.id)
    )
    return result.scalars().all()


@router.delete("/{stock_id}", status_code=204)
async def delete_stock(
    stock_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WatchStock).where(
            WatchStock.id == stock_id,
            WatchStock.user_id == current_user.id,
        )
    )
    stock = result.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail="종목을 찾을 수 없습니다.")

    await db.delete(stock)
    await db.commit()


@router.get("/{ticker}/signals", response_model=List[SignalResponse])
async def get_signals(
    ticker: str,
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """특정 종목의 최근 시그널 목록을 반환합니다."""
    # 프리미엄 사용자만 실시간 알림 (조회는 모두 가능)
    result = await db.execute(
        select(TradeSignal)
        .where(TradeSignal.ticker == ticker.upper())
        .order_by(desc(TradeSignal.created_at))
        .limit(limit)
    )
    return result.scalars().all()


@router.post("/{ticker}/refresh", response_model=SignalResponse)
async def refresh_signal(
    ticker: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """특정 종목의 시그널을 즉시 갱신합니다."""
    # 해당 종목이 사용자 관심 목록에 있는지 확인
    result = await db.execute(
        select(WatchStock).where(
            WatchStock.user_id == current_user.id,
            WatchStock.ticker == ticker.upper(),
        )
    )
    watch = result.scalar_one_or_none()
    if not watch:
        raise HTTPException(status_code=404, detail="관심 종목에 없는 종목입니다.")

    from app.services.signal_engine import generate_signal

    signal_data = generate_signal(ticker.upper(), watch.market.value)
    if not signal_data:
        raise HTTPException(status_code=503, detail="시그널 생성에 실패했습니다. 잠시 후 다시 시도하세요.")

    signal = TradeSignal(
        ticker=signal_data["ticker"],
        action=signal_data["action"],
        score=signal_data["score"],
        reason=signal_data["reason"],
        current_price=signal_data.get("current_price"),
        price_change_5d=signal_data.get("price_change_5d"),
        rsi=signal_data.get("rsi"),
        news_sentiment=signal_data.get("news_sentiment"),
    )
    db.add(signal)
    await db.commit()
    await db.refresh(signal)

    # 프리미엄 사용자에게 텔레그램 알림 (백그라운드)
    if current_user.plan == PlanType.PREMIUM and current_user.telegram_chat_id:
        from app.services.notifier import notify_buy_signal
        background_tasks.add_task(
            notify_buy_signal,
            signal_data,
            current_user.telegram_chat_id,
            watch.name,
        )

    return signal
