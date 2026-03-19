from abc import abstractmethod
from typing import Optional, List

from app.domain.ports.base_service import AbstractService


class AbstractStockDataService(AbstractService):
    """
    헥사고날 아키텍처 - 주식 데이터 서비스 포트
    주가 수집, 분석, 시그널 생성 유스케이스 경계 정의
    """

    @abstractmethod
    def fetch_stock_data(self, ticker: str, market: str = "US") -> Optional[dict]:
        """
        티커와 시장 정보를 받아 주가 데이터를 수집합니다.

        Returns:
            {
                "ticker": str, "current_price": float,
                "change_pct": float, "volume": int,
                "prices_5d": list[float], "rsi": float | None,
            }
        """
        raise NotImplementedError

    @abstractmethod
    def generate_signal(
        self,
        ticker: str,
        market: str,
        news_sentiment_score: float = 50.0,
    ) -> Optional[dict]:
        """
        티커에 대한 매수/매도/관망 시그널을 생성합니다.

        Returns:
            {"ticker": str, "action": str, "score": float, "reason": str}
        """
        raise NotImplementedError

    @abstractmethod
    def analyze_market_news(self) -> dict:
        """
        최신 뉴스를 분석하여 시장 센티먼트를 반환합니다.

        Returns:
            {"summary": str, "sentiment": str, "sentiment_score": float}
        """
        raise NotImplementedError

    @abstractmethod
    async def notify_signal(
        self,
        signal_data: dict,
        chat_id: str,
        stock_name: str,
    ) -> bool:
        """텔레그램으로 매수 시그널 알림을 전송합니다."""
        raise NotImplementedError

    @abstractmethod
    def get_watchlist(self, user_id: int) -> List[dict]:
        """사용자의 관심 종목 목록을 반환합니다."""
        raise NotImplementedError
