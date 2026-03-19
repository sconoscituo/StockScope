"""관심 종목 모니터링"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import yfinance as yf

scheduler = AsyncIOScheduler()

async def check_price_alerts(db_session):
    """목표가 도달 시 알림 (스케줄러에서 5분마다 실행)"""
    # DB에서 활성 알림 조회 후 현재가 비교
    pass  # 실제 구현은 DB 연결 필요

def get_stock_info(ticker: str) -> dict:
    """주식 기본 정보 조회"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "ticker": ticker,
            "name": info.get("longName", ""),
            "price": info.get("currentPrice", 0),
            "change_pct": info.get("52WeekChange", 0),
            "market_cap": info.get("marketCap", 0),
            "pe_ratio": info.get("trailingPE", 0),
        }
    except Exception:
        return {"ticker": ticker, "error": "조회 실패"}
