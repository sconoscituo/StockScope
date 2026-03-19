from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class TradeType(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    ticker = Column(String, nullable=False, index=True)
    name = Column(String, nullable=True)
    trade_type = Column(Enum(TradeType), nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)          # 매수/매도 단가
    target_price = Column(Float, nullable=True)    # 목표가 알림
    memo = Column(String, nullable=True)
    traded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", backref="portfolios")
