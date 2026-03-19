"""
포트원(PortOne) 결제 연동 서비스
실제 사용 시 PORTONE_API_KEY, PORTONE_API_SECRET 환경변수 필요
"""
import httpx
from app.config import settings

PORTONE_API_URL = "https://api.iamport.kr"


async def get_access_token() -> str:
    """포트원 액세스 토큰 발급"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PORTONE_API_URL}/users/getToken",
            json={
                "imp_key": settings.PORTONE_API_KEY,
                "imp_secret": settings.PORTONE_API_SECRET,
            },
        )
        response.raise_for_status()
        data = response.json()
        if data.get("code") != 0:
            raise ValueError(f"포트원 토큰 발급 실패: {data.get('message')}")
        return data["response"]["access_token"]


async def verify_payment(imp_uid: str, expected_amount: int) -> bool:
    """결제 검증 - 결제금액 위변조 방지"""
    token = await get_access_token()
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{PORTONE_API_URL}/payments/{imp_uid}",
            headers={"Authorization": token},
        )
        response.raise_for_status()
        data = response.json()
        if data.get("code") != 0:
            return False
        payment = data["response"]
        # 결제 상태가 paid이고 금액이 일치하는지 검증
        return (
            payment.get("status") == "paid"
            and payment.get("amount") == expected_amount
        )


async def cancel_payment(imp_uid: str, reason: str) -> dict:
    """결제 취소"""
    token = await get_access_token()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PORTONE_API_URL}/payments/cancel",
            headers={"Authorization": token},
            json={"imp_uid": imp_uid, "reason": reason},
        )
        response.raise_for_status()
        data = response.json()
        if data.get("code") != 0:
            raise ValueError(f"결제 취소 실패: {data.get('message')}")
        return data["response"]
