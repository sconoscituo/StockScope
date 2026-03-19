from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from datetime import datetime

from app.database import Base


class MarketAnalysis(Base):
    __tablename__ = "market_analyses"

    id = Column(Integer, primary_key=True, index=True)
    summary = Column(Text, nullable=False)
    sentiment = Column(String, nullable=False)  # FEAR / NEUTRAL / GREED
    sentiment_score = Column(Float, nullable=True)  # 0-100 (fear=0, greed=100)
    key_events = Column(Text, nullable=True)  # JSON string of key events list
    source_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
