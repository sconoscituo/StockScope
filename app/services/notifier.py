"""
텔레그램 봇으로 매수 시그널 알림을 발송합니다.
BUY 시그널이 설정된 임계값(기본 80점) 이상일 때만 발송합니다.
"""
import logging
import asyncio
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


def _format_signal_message(signal: dict, stock_name: str = "") -> str:
    """텔레그램 메시지를 포맷합니다."""
    action_emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}.get(signal["action"], "⚪")
    ticker = signal.get("ticker", "")
    name_part = f" ({stock_name})" if stock_name else ""

    lines = [
        f"{action_emoji} *StockScope 시그널 알림*",
        f"",
        f"📌 종목: `{ticker}`{name_part}",
        f"📊 시그널: *{signal['action']}*",
        f"💯 신뢰도: {signal['score']:.0f}/100",
        f"",
        f"📋 근거:",
        f"{signal.get('reason', '')}",
        f"",
    ]

    if signal.get("current_price") is not None:
        lines.append(f"💰 현재가: {signal['current_price']:,.2f}")
    if signal.get("price_change_5d") is not None:
        change = signal["price_change_5d"]
        emoji = "📈" if change >= 0 else "📉"
        lines.append(f"{emoji} 5일 변화율: {change:+.2f}%")
    if signal.get("rsi") is not None:
        lines.append(f"📉 RSI: {signal['rsi']:.1f}")

    lines.append(f"")
    lines.append(f"⏰ _StockScope AI 분석 (투자 참고용, 책임은 본인에게 있습니다)_")

    return "\n".join(lines)


async def send_telegram_message(chat_id: str, message: str) -> bool:
    """텔레그램으로 메시지를 발송합니다."""
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not set, skipping notification")
        return False

    try:
        from telegram import Bot
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="Markdown",
        )
        logger.info(f"Telegram message sent to chat_id={chat_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send Telegram message to {chat_id}: {e}")
        return False


async def notify_buy_signal(
    signal: dict,
    chat_id: str,
    stock_name: str = "",
    threshold: int = None,
) -> bool:
    """
    BUY 시그널이 임계값 이상일 때 텔레그램으로 알림을 발송합니다.

    Args:
        signal: signal_engine.generate_signal()의 반환값
        chat_id: 텔레그램 chat_id
        stock_name: 종목명 (선택)
        threshold: 알림 발송 최소 점수 (기본: 설정값)

    Returns:
        bool: 발송 여부
    """
    if threshold is None:
        threshold = settings.BUY_SIGNAL_NOTIFY_THRESHOLD

    if signal.get("action") != "BUY":
        return False

    if signal.get("score", 0) < threshold:
        logger.debug(
            f"Signal score {signal.get('score')} below threshold {threshold}, skipping"
        )
        return False

    message = _format_signal_message(signal, stock_name)
    return await send_telegram_message(chat_id, message)


async def notify_market_analysis(chat_id: str, analysis: dict) -> bool:
    """시장 분석 결과를 텔레그램으로 발송합니다."""
    sentiment_emoji = {
        "FEAR": "😨",
        "NEUTRAL": "😐",
        "GREED": "🤑",
    }.get(analysis.get("sentiment", "NEUTRAL"), "❓")

    lines = [
        f"{sentiment_emoji} *StockScope 시장 분석*",
        f"",
        f"📊 시장 감성: *{analysis.get('sentiment', 'NEUTRAL')}*",
        f"📈 탐욕/공포 지수: {analysis.get('sentiment_score', 50):.0f}/100",
        f"",
        f"📝 요약:",
        f"{analysis.get('summary', '')}",
    ]

    key_events = analysis.get("key_events", [])
    if key_events:
        lines.append("")
        lines.append("🔑 주요 이벤트:")
        for event in key_events[:5]:
            lines.append(f"  • {event}")

    lines.append(f"")
    lines.append(f"⏰ _StockScope AI 시장 분석_")

    message = "\n".join(lines)
    return await send_telegram_message(chat_id, message)
