from enum import Enum

class PlanType(str, Enum):
    FREE = "free"
    PRO = "pro"          # 월 9,900원
    PREMIUM = "premium"  # 월 19,900원

PLAN_LIMITS = {
    PlanType.FREE:    {"watchlist": 5,  "ai_analysis": False, "price_alerts": 3,  "portfolio_stocks": 5},
    PlanType.PRO:     {"watchlist": 50, "ai_analysis": True,  "price_alerts": 20, "portfolio_stocks": 30},
    PlanType.PREMIUM: {"watchlist": 999,"ai_analysis": True,  "price_alerts": 99, "portfolio_stocks": 999},
}
PLAN_PRICES_KRW = {PlanType.FREE: 0, PlanType.PRO: 9900, PlanType.PREMIUM: 19900}
