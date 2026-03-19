from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Enum
from datetime import datetime
import enum

from app.database import Base


class SignalAction(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class TradeSignal(Base):
    __tablename__ = "trade_signals"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, nullable=False, index=True)
    action = Column(Enum(SignalAction), nullable=False)
    score = Column(Float, nullable=False)  # 0-100 confidence score
    reason = Column(Text, nullable=False)
    current_price = Column(Float, nullable=True)
    price_change_5d = Column(Float, nullable=True)  # 5-day price change %
    rsi = Column(Float, nullable=True)
    news_sentiment = Column(Float, nullable=True)  # -1.0 to 1.0
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
