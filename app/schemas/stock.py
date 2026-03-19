from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.stock import MarketType
from app.models.signal import SignalAction


class StockAdd(BaseModel):
    ticker: str
    name: str
    market: MarketType


class StockResponse(BaseModel):
    id: int
    ticker: str
    name: str
    market: MarketType
    created_at: datetime

    model_config = {"from_attributes": True}


class SignalResponse(BaseModel):
    id: int
    ticker: str
    action: SignalAction
    score: float
    reason: str
    current_price: Optional[float] = None
    price_change_5d: Optional[float] = None
    rsi: Optional[float] = None
    news_sentiment: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MarketAnalysisResponse(BaseModel):
    id: int
    summary: str
    sentiment: str
    sentiment_score: Optional[float] = None
    key_events: Optional[str] = None
    source_count: int
    created_at: datetime

    model_config = {"from_attributes": True}
