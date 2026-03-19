from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class MarketType(str, enum.Enum):
    KR = "KR"
    US = "US"


class WatchStock(Base):
    __tablename__ = "watch_stocks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ticker = Column(String, nullable=False)
    name = Column(String, nullable=False)
    market = Column(Enum(MarketType), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="watch_stocks")
