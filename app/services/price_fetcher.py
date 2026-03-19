"""
yfinance를 사용하여 주가 데이터를 수집합니다.
한국 주식: '005930.KS' 형식, 미국 주식: 'AAPL' 형식
"""
import yfinance as yf
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def _normalize_ticker(ticker: str, market: str) -> str:
    """한국 주식 티커에 .KS 접미사를 자동 추가합니다."""
    if market == "KR" and not ticker.endswith(".KS") and not ticker.endswith(".KQ"):
        return f"{ticker}.KS"
    return ticker


def fetch_stock_data(ticker: str, market: str = "US") -> Optional[dict]:
    """
    주어진 티커의 주가 데이터를 수집합니다.

    Returns:
        {
            "ticker": str,
            "current_price": float,
            "prev_close": float,
            "change_pct": float,
            "volume": int,
            "high_52w": float,
            "low_52w": float,
            "prices_5d": list[float],   # 최근 5일 종가
            "volumes_5d": list[int],
            "market_cap": float | None,
        }
    """
    normalized = _normalize_ticker(ticker, market)
    try:
        stock = yf.Ticker(normalized)
        hist = stock.history(period="1mo")

        if hist.empty:
            logger.warning(f"No data found for ticker: {normalized}")
            return None

        prices_5d = hist["Close"].tail(5).tolist()
        volumes_5d = hist["Volume"].tail(5).tolist()

        current_price = prices_5d[-1] if prices_5d else None
        prev_close = prices_5d[-2] if len(prices_5d) >= 2 else current_price
        change_pct = (
            ((current_price - prev_close) / prev_close * 100)
            if prev_close and prev_close != 0
            else 0.0
        )

        info = stock.info
        high_52w = info.get("fiftyTwoWeekHigh") or hist["High"].max()
        low_52w = info.get("fiftyTwoWeekLow") or hist["Low"].min()
        market_cap = info.get("marketCap")

        return {
            "ticker": ticker,
            "normalized_ticker": normalized,
            "current_price": round(current_price, 2) if current_price else None,
            "prev_close": round(prev_close, 2) if prev_close else None,
            "change_pct": round(change_pct, 2),
            "volume": int(volumes_5d[-1]) if volumes_5d else 0,
            "high_52w": round(high_52w, 2) if high_52w else None,
            "low_52w": round(low_52w, 2) if low_52w else None,
            "prices_5d": [round(p, 2) for p in prices_5d],
            "volumes_5d": [int(v) for v in volumes_5d],
            "market_cap": market_cap,
        }
    except Exception as e:
        logger.error(f"Failed to fetch data for {normalized}: {e}")
        return None


def calculate_rsi(prices: list[float], period: int = 14) -> Optional[float]:
    """
    RSI(Relative Strength Index)를 계산합니다.
    period보다 짧은 데이터는 None을 반환합니다.
    """
    if len(prices) < period + 1:
        return None

    gains = []
    losses = []
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i - 1]
        if diff > 0:
            gains.append(diff)
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(abs(diff))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 2)


def get_moving_averages(prices: list[float]) -> dict:
    """이동평균 계산 (5일, 20일)."""
    result = {"ma5": None, "ma20": None}
    if len(prices) >= 5:
        result["ma5"] = round(sum(prices[-5:]) / 5, 2)
    if len(prices) >= 20:
        result["ma20"] = round(sum(prices[-20:]) / 20, 2)
    return result
