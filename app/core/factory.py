"""
팩토리 패턴 - 서비스 인스턴스 생성 및 싱글톤 관리
헥사고날 아키텍처의 컴포지션 루트 역할
"""
from typing import Type, TypeVar, Dict, Any

T = TypeVar("T")

_instances: Dict[type, Any] = {}


class ServiceFactory:
    """서비스 싱글톤 팩토리"""

    @classmethod
    def get_instance(cls, service_class: Type[T]) -> T:
        """싱글톤 인스턴스 반환 - 없으면 생성"""
        if service_class not in _instances:
            _instances[service_class] = service_class()
        return _instances[service_class]

    @classmethod
    def clear(cls) -> None:
        """테스트용 인스턴스 초기화"""
        _instances.clear()

    # --- StockScope 전용 팩토리 메서드 ---

    @classmethod
    def create_price_fetcher(cls):
        """주가 데이터 수집 서비스 반환"""
        from app.services import price_fetcher
        return price_fetcher

    @classmethod
    def create_analyzer(cls):
        """주식 분석 서비스 반환"""
        from app.services import analyzer
        return analyzer

    @classmethod
    def create_signal_engine(cls):
        """매수매도 시그널 엔진 반환"""
        from app.services import signal_engine
        return signal_engine

    @classmethod
    def create_news_analyzer(cls):
        """뉴스 분석 서비스 반환"""
        from app.services import news_analyzer
        return news_analyzer

    @classmethod
    def create_notifier(cls):
        """텔레그램 알림 서비스 반환"""
        from app.services import notifier
        return notifier

    @classmethod
    def create_watchlist_service(cls):
        """관심 종목 서비스 반환"""
        from app.services import watchlist
        return watchlist

    @classmethod
    def create_payment_service(cls):
        """결제 서비스 반환"""
        from app.services import payment
        return payment

    @classmethod
    def create_subscription_service(cls):
        """구독 서비스 반환"""
        from app.services import subscription
        return subscription
