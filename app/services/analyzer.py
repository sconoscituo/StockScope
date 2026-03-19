"""
Gemini API를 활용한 주식 AI 분석 리포트 + 재무제표 분석 서비스
"""
import logging
from typing import Optional
import yfinance as yf
import google.generativeai as genai

from app.config import settings

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.GEMINI_API_KEY)


def _get_financial_summary(ticker: str) -> dict:
    """yfinance로 주요 재무 지표를 가져옵니다."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "marketCap": info.get("marketCap"),
            "trailingPE": info.get("trailingPE"),
            "forwardPE": info.get("forwardPE"),
            "priceToBook": info.get("priceToBook"),
            "dividendYield": info.get("dividendYield"),
            "revenueGrowth": info.get("revenueGrowth"),
            "earningsGrowth": info.get("earningsGrowth"),
            "debtToEquity": info.get("debtToEquity"),
            "returnOnEquity": info.get("returnOnEquity"),
            "currentPrice": info.get("currentPrice"),
            "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh"),
            "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow"),
            "shortName": info.get("shortName", ticker),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
        }
    except Exception as e:
        logger.warning(f"Failed to fetch financial data for {ticker}: {e}")
        return {}


def generate_stock_report(ticker: str, lang: str = "ko") -> str:
    """
    Gemini API로 주식 분석 리포트를 생성합니다.
    - 재무 지표 기반 기업 분석
    - 투자 매력도 평가
    - 리스크 요인
    """
    fin = _get_financial_summary(ticker)

    prompt = f"""
당신은 전문 주식 애널리스트입니다. 아래 재무 데이터를 바탕으로 {ticker} 종목에 대한 투자 분석 리포트를 작성하세요.

## 재무 데이터
- 종목명: {fin.get('shortName', ticker)}
- 현재가: {fin.get('currentPrice')}
- 섹터: {fin.get('sector')} / 업종: {fin.get('industry')}
- 시가총액: {fin.get('marketCap')}
- PER (trailing): {fin.get('trailingPE')}
- PER (forward): {fin.get('forwardPE')}
- PBR: {fin.get('priceToBook')}
- 배당수익률: {fin.get('dividendYield')}
- 매출 성장률: {fin.get('revenueGrowth')}
- 이익 성장률: {fin.get('earningsGrowth')}
- 부채비율(D/E): {fin.get('debtToEquity')}
- ROE: {fin.get('returnOnEquity')}
- 52주 최고: {fin.get('fiftyTwoWeekHigh')} / 52주 최저: {fin.get('fiftyTwoWeekLow')}

## 리포트 작성 지침
1. **기업 개요** (2~3문장)
2. **재무 건전성 분석** (PER·PBR·부채비율·ROE 해석)
3. **성장성 평가** (매출·이익 성장률 분석)
4. **투자 매력도** (긍정 요인 3가지)
5. **리스크 요인** (부정 요인 3가지)
6. **종합 의견** (매수/중립/매도 + 근거 1문장)

리포트는 한국어로 작성하고, 마크다운 형식을 사용하세요.
"""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Gemini analysis failed for {ticker}: {e}")
        return f"[분석 실패] {ticker} 종목 분석 중 오류가 발생했습니다: {str(e)}"


def recommend_stocks(sector: Optional[str] = None) -> str:
    """
    Gemini API로 AI 종목 추천 (프리미엄 기능)
    """
    sector_text = f"'{sector}' 섹터에서" if sector else "전체 시장에서"
    prompt = f"""
당신은 전문 주식 애널리스트입니다.
현재 시장 상황을 고려하여 {sector_text} 투자 매력이 높은 한국/미국 주식 5종목을 추천해주세요.

각 종목에 대해:
1. 종목명 및 티커
2. 추천 이유 (2~3문장)
3. 목표 수익률
4. 주요 리스크

마크다운 형식으로 작성하세요.
"""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Gemini stock recommendation failed: {e}")
        return f"[추천 실패] 종목 추천 중 오류가 발생했습니다: {str(e)}"
