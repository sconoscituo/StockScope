"""
Gemini AI를 사용하여 매수/매도/보유 시그널을 생성합니다.
기술적 분석 (RSI, 이동평균, 추세) + 뉴스 감성 점수 종합.
"""
import logging
import json
from typing import Optional
import google.generativeai as genai

from app.config import settings
from app.services.price_fetcher import (
    fetch_stock_data,
    calculate_rsi,
    get_moving_averages,
)

logger = logging.getLogger(__name__)


def generate_signal(
    ticker: str,
    market: str = "US",
    news_sentiment_score: Optional[float] = None,
) -> Optional[dict]:
    """
    주어진 티커에 대한 매수/매도/보유 시그널을 생성합니다.

    Returns:
        {
            "ticker": str,
            "action": "BUY" | "SELL" | "HOLD",
            "score": float (0-100),
            "reason": str,
            "current_price": float | None,
            "price_change_5d": float | None,
            "rsi": float | None,
            "news_sentiment": float | None,  # -1.0 ~ 1.0
        }
    """
    # 주가 데이터 수집
    price_data = fetch_stock_data(ticker, market)
    if not price_data:
        logger.warning(f"No price data available for {ticker}")
        return None

    prices_5d = price_data.get("prices_5d", [])
    current_price = price_data.get("current_price")

    # 기술적 지표 계산
    rsi = calculate_rsi(prices_5d) if len(prices_5d) >= 5 else None
    ma = get_moving_averages(prices_5d)

    # 5일 가격 변화율
    price_change_5d = None
    if len(prices_5d) >= 2:
        first_price = prices_5d[0]
        last_price = prices_5d[-1]
        if first_price and first_price != 0:
            price_change_5d = round((last_price - first_price) / first_price * 100, 2)

    # 뉴스 감성을 -1~1 범위로 변환 (sentiment_score는 0~100)
    news_sentiment_normalized = None
    if news_sentiment_score is not None:
        news_sentiment_normalized = round((news_sentiment_score - 50) / 50, 3)

    if not settings.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not set, using rule-based signal")
        return _rule_based_signal(
            ticker, price_data, rsi, ma, price_change_5d, news_sentiment_normalized
        )

    return _gemini_signal(
        ticker, price_data, rsi, ma, price_change_5d, news_sentiment_normalized
    )


def _gemini_signal(
    ticker: str,
    price_data: dict,
    rsi: Optional[float],
    ma: dict,
    price_change_5d: Optional[float],
    news_sentiment: Optional[float],
) -> Optional[dict]:
    """Gemini AI를 사용하여 시그널을 생성합니다."""
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")

    context = f"""종목: {ticker}
시장: {price_data.get('normalized_ticker', ticker)}
현재가: {price_data.get('current_price')}
전일 대비: {price_data.get('change_pct')}%
최근 5일 종가: {price_data.get('prices_5d')}
5일 가격변화율: {price_change_5d}%
RSI(14): {rsi if rsi else '데이터 부족'}
5일 이동평균: {ma.get('ma5')}
20일 이동평균: {ma.get('ma20')}
52주 최고: {price_data.get('high_52w')}
52주 최저: {price_data.get('low_52w')}
뉴스 감성 점수: {news_sentiment if news_sentiment is not None else '없음'} (-1=극도공포, 0=중립, 1=극도탐욕)"""

    prompt = f"""다음 주식 데이터를 분석하여 매수/매도/보유 시그널을 생성해주세요.

{context}

분석 기준:
- RSI 30 미만: 과매도 (매수 신호)
- RSI 70 초과: 과매수 (매도 신호)
- 5일 이동평균 > 20일 이동평균: 단기 상승 추세
- 뉴스 감성이 부정적이면 매도 압력 증가

다음 JSON 형식으로만 응답하세요:
{{
  "action": "BUY 또는 SELL 또는 HOLD",
  "score": 0~100 사이 신뢰도 숫자,
  "reason": "매수/매도/보유 근거 한글 2-3문장"
}}"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()

        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        result = json.loads(text)

        action = result.get("action", "HOLD")
        if action not in ("BUY", "SELL", "HOLD"):
            action = "HOLD"

        score = float(result.get("score", 50))
        score = max(0.0, min(100.0, score))

        return {
            "ticker": ticker,
            "action": action,
            "score": round(score, 1),
            "reason": result.get("reason", ""),
            "current_price": price_data.get("current_price"),
            "price_change_5d": price_change_5d,
            "rsi": rsi,
            "news_sentiment": news_sentiment,
        }

    except Exception as e:
        logger.error(f"Gemini signal generation failed for {ticker}: {e}")
        return _rule_based_signal(
            ticker, price_data, rsi, ma, price_change_5d, news_sentiment
        )


def _rule_based_signal(
    ticker: str,
    price_data: dict,
    rsi: Optional[float],
    ma: dict,
    price_change_5d: Optional[float],
    news_sentiment: Optional[float],
) -> dict:
    """Gemini API 없이 규칙 기반으로 시그널을 생성합니다 (폴백)."""
    score = 50.0
    signals = []

    if rsi is not None:
        if rsi < 30:
            score += 20
            signals.append(f"RSI {rsi:.1f} - 과매도 구간")
        elif rsi > 70:
            score -= 20
            signals.append(f"RSI {rsi:.1f} - 과매수 구간")
        else:
            signals.append(f"RSI {rsi:.1f} - 정상 범위")

    ma5 = ma.get("ma5")
    ma20 = ma.get("ma20")
    if ma5 and ma20:
        if ma5 > ma20:
            score += 10
            signals.append("단기 이동평균 > 장기 이동평균 (상승 추세)")
        else:
            score -= 10
            signals.append("단기 이동평균 < 장기 이동평균 (하락 추세)")

    if price_change_5d is not None:
        if price_change_5d > 3:
            score += 5
            signals.append(f"5일 상승률 {price_change_5d:.1f}%")
        elif price_change_5d < -3:
            score -= 5
            signals.append(f"5일 하락률 {price_change_5d:.1f}%")

    if news_sentiment is not None:
        score += news_sentiment * 10
        signals.append(f"뉴스 감성 점수 {news_sentiment:.2f}")

    score = max(0.0, min(100.0, score))

    if score >= 65:
        action = "BUY"
    elif score <= 35:
        action = "SELL"
    else:
        action = "HOLD"

    reason = " | ".join(signals) if signals else "기술적 지표 기반 분석"

    return {
        "ticker": ticker,
        "action": action,
        "score": round(score, 1),
        "reason": reason,
        "current_price": price_data.get("current_price"),
        "price_change_5d": price_change_5d,
        "rsi": rsi,
        "news_sentiment": news_sentiment,
    }
