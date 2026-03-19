from sqlalchemy import Column, Integer, String, DateTime, Enum
from datetime import datetime
import enum

from app.database import Base


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"
    FAILED = "failed"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    imp_uid = Column(String, unique=True, index=True, nullable=False)  # 포트원 결제 고유번호
    merchant_uid = Column(String, unique=True, index=True, nullable=False)  # 주문번호
    user_id = Column(Integer, nullable=False, index=True)
    amount = Column(Integer, nullable=False)  # 결제금액 (원)
    plan = Column(String, nullable=False)  # 구독 플랜명
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    cancel_reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
