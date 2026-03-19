import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select
import json

from app.config import settings
from app.database import init_db, AsyncSessionLocal
from app.routers import users, stocks, analysis, portfolio, payments

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def update_all_signals():
    """30분마다 모든 관심 종목의 시그널을 업데이트합니다."""
    logger.info("Starting scheduled signal update for all watch stocks...")

    from app.models.stock import WatchStock
    from app.models.signal import TradeSignal
    from app.models.user import User, PlanType
    from app.models.analysis import MarketAnalysis
    from app.services.signal_engine import generate_signal
    from app.services.news_analyzer import run_news_analysis
    from app.services.notifier import notify_buy_signal

    async with AsyncSessionLocal() as db:
        # 시장 분석 실행
        try:
            analysis_data = run_news_analysis()
            key_events_json = json.dumps(
                analysis_data.get("key_events", []), ensure_ascii=False
            )
            market_analysis = MarketAnalysis(
                summary=analysis_data.get("summary", ""),
                sentiment=analysis_data.get("sentiment", "NEUTRAL"),
                sentiment_score=analysis_data.get("sentiment_score"),
                key_events=key_events_json,
                source_count=analysis_data.get("source_count", 0),
            )
            db.add(market_analysis)
            await db.commit()
            news_sentiment_score = analysis_data.get("sentiment_score", 50.0)
            logger.info(
                f"Market analysis saved: {analysis_data.get('sentiment')} "
                f"({news_sentiment_score})"
            )
        except Exception as e:
            logger.error(f"Market analysis failed: {e}")
            news_sentiment_score = 50.0

        # 모든 관심 종목 조회
        result = await db.execute(select(WatchStock))
        watch_stocks = result.scalars().all()

        # 프리미엄 사용자 조회 (telegram_chat_id 있는 경우)
        premium_result = await db.execute(
            select(User).where(
                User.plan == PlanType.PREMIUM,
                User.telegram_chat_id.isnot(None),
                User.is_active == True,
            )
        )
        premium_users = {u.id: u for u in premium_result.scalars().all()}

        updated = 0
        for watch in watch_stocks:
            try:
                signal_data = generate_signal(
                    watch.ticker,
                    watch.market.value,
                    news_sentiment_score=news_sentiment_score,
                )
                if not signal_data:
                    continue

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
                updated += 1

                # 프리미엄 사용자 텔레그램 알림
                user = premium_users.get(watch.user_id)
                if user and user.telegram_chat_id:
                    import asyncio
                    asyncio.create_task(
                        notify_buy_signal(
                            signal_data,
                            user.telegram_chat_id,
                            watch.name,
                        )
                    )

            except Exception as e:
                logger.error(f"Signal update failed for {watch.ticker}: {e}")

        logger.info(f"Scheduled signal update complete: {updated}/{len(watch_stocks)} updated")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized.")

    # 30분마다 시그널 업데이트
    scheduler.add_job(
        update_all_signals,
        trigger=IntervalTrigger(minutes=30),
        id="update_signals",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.start()
    logger.info("Scheduler started (signal update every 30 minutes).")

    yield

    # Shutdown
    scheduler.shutdown()
    logger.info("Scheduler stopped.")


app = FastAPI(
    title="StockScope API",
    description="한국/미국 주식 AI 분석 + 매수매도 시그널 + 텔레그램 알림",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(stocks.router)
app.include_router(analysis.router)
app.include_router(portfolio.router)
app.include_router(payments.router)


@app.get("/", tags=["health"])
async def root():
    return {
        "service": "StockScope",
        "version": "1.0.0",
        "status": "running",
        "description": "한국/미국 주식 AI 분석 + 매수매도 시그널 서비스",
    }


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
