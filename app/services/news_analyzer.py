"""
경제 뉴스 RSS 수집 + Gemini AI 감성 분석 (공포/탐욕 지수)
"""
import feedparser
import logging
from typing import Optional
import google.generativeai as genai
import json

from app.config import settings

logger = logging.getLogger(__name__)

RSS_FEEDS = {
    "연합뉴스_경제": "https://www.yonhapnewstv.co.kr/category/news/economy/feed/",
    "한국경제": "https://www.hankyung.com/feed/economy",
    "Bloomberg_Markets": "https://feeds.bloomberg.com/markets/news.rss",
    "Reuters_Business": "https://feeds.reuters.com/reuters/businessNews",
}

FALLBACK_FEEDS = {
    "연합뉴스_경제": "https://www.yna.co.kr/rss/economy.xml",
    "Yahoo_Finance": "https://finance.yahoo.com/news/rssindex",
}


def fetch_news_headlines(max_per_feed: int = 5) -> list[dict]:
    """RSS 피드에서 뉴스 헤드라인을 수집합니다."""
    headlines = []
    feeds_to_try = {**RSS_FEEDS, **FALLBACK_FEEDS}

    for source, url in feeds_to_try.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_per_feed]:
                title = entry.get("title", "").strip()
                summary = entry.get("summary", "")[:200].strip()
                if title:
                    headlines.append({
                        "source": source,
                        "title": title,
                        "summary": summary,
                    })
        except Exception as e:
            logger.warning(f"Failed to fetch RSS from {source} ({url}): {e}")

    logger.info(f"Fetched {len(headlines)} headlines from {len(feeds_to_try)} feeds")
    return headlines


def analyze_market_sentiment(headlines: list[dict]) -> dict:
    """
    Gemini AI로 뉴스 헤드라인의 시장 감성을 분석합니다.

    Returns:
        {
            "sentiment": "FEAR" | "NEUTRAL" | "GREED",
            "sentiment_score": float (0=극도공포, 50=중립, 100=극도탐욕),
            "summary": str,
            "key_events": list[str],
        }
    """
    if not headlines:
        return {
            "sentiment": "NEUTRAL",
            "sentiment_score": 50.0,
            "summary": "수집된 뉴스가 없어 분석할 수 없습니다.",
            "key_events": [],
        }

    if not settings.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not set, returning neutral sentiment")
        return {
            "sentiment": "NEUTRAL",
            "sentiment_score": 50.0,
            "summary": "API 키가 설정되지 않아 분석을 수행할 수 없습니다.",
            "key_events": [],
        }

    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")

    headlines_text = "\n".join(
        f"[{h['source']}] {h['title']}" for h in headlines[:30]
    )

    prompt = f"""다음은 오늘의 경제/금융 뉴스 헤드라인입니다. 주식 시장 감성을 분석해주세요.

뉴스 헤드라인:
{headlines_text}

다음 JSON 형식으로 정확히 응답하세요 (다른 텍스트 없이):
{{
  "sentiment": "FEAR 또는 NEUTRAL 또는 GREED 중 하나",
  "sentiment_score": 0~100 사이 숫자 (0=극도공포, 50=중립, 100=극도탐욕),
  "summary": "시장 상황 한글 요약 2-3문장",
  "key_events": ["주요 이벤트 1", "주요 이벤트 2", "주요 이벤트 3"]
}}"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()

        # JSON 블록 추출
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        result = json.loads(text)

        # 유효성 검사 및 기본값 설정
        sentiment = result.get("sentiment", "NEUTRAL")
        if sentiment not in ("FEAR", "NEUTRAL", "GREED"):
            sentiment = "NEUTRAL"

        score = float(result.get("sentiment_score", 50))
        score = max(0.0, min(100.0, score))

        return {
            "sentiment": sentiment,
            "sentiment_score": round(score, 1),
            "summary": result.get("summary", ""),
            "key_events": result.get("key_events", []),
            "source_count": len(headlines),
        }

    except Exception as e:
        logger.error(f"Gemini sentiment analysis failed: {e}")
        return {
            "sentiment": "NEUTRAL",
            "sentiment_score": 50.0,
            "summary": f"분석 중 오류가 발생했습니다: {str(e)}",
            "key_events": [],
            "source_count": len(headlines),
        }


def run_news_analysis() -> dict:
    """뉴스 수집 + 감성 분석을 한 번에 실행합니다."""
    headlines = fetch_news_headlines()
    return analyze_market_sentiment(headlines)
