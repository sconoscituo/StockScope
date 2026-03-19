import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

import yfinance as yf

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, symbol: str):
        await websocket.accept()
        if symbol not in self.active_connections:
            self.active_connections[symbol] = []
        self.active_connections[symbol].append(websocket)
        logger.info(f"WebSocket connected: {symbol} (total: {len(self.active_connections[symbol])})")

    def disconnect(self, websocket: WebSocket, symbol: str):
        if symbol in self.active_connections:
            try:
                self.active_connections[symbol].remove(websocket)
            except ValueError:
                pass
            if not self.active_connections[symbol]:
                del self.active_connections[symbol]
        logger.info(f"WebSocket disconnected: {symbol}")

    async def broadcast(self, symbol: str, data: dict):
        if symbol not in self.active_connections:
            return
        dead = []
        for ws in self.active_connections[symbol]:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            try:
                self.active_connections[symbol].remove(ws)
            except ValueError:
                pass


manager = ConnectionManager()


def _fetch_price(symbol: str) -> dict | None:
    """yfinance로 현재 가격 정보를 동기 방식으로 조회합니다."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info
        last_price = info.last_price
        previous_close = info.previous_close
        if last_price is None or previous_close is None:
            return None
        change = last_price - previous_close
        change_pct = (change / previous_close) * 100 if previous_close else 0.0
        return {
            "symbol": symbol,
            "price": round(last_price, 4),
            "change": round(change, 4),
            "change_pct": round(change_pct, 4),
        }
    except Exception as e:
        logger.warning(f"Failed to fetch price for {symbol}: {e}")
        return None


@router.websocket("/ws/stock/{symbol}")
async def stock_websocket(websocket: WebSocket, symbol: str):
    """
    실시간 주식 가격을 10초마다 WebSocket으로 브로드캐스트합니다.

    - symbol: 종목 티커 (예: AAPL, 005930.KS)
    """
    symbol = symbol.upper()
    await manager.connect(websocket, symbol)
    try:
        while True:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, _fetch_price, symbol)
            if data:
                await manager.broadcast(symbol, data)
            else:
                await websocket.send_json(
                    {"symbol": symbol, "error": "가격 데이터를 가져올 수 없습니다."}
                )
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        manager.disconnect(websocket, symbol)
    except Exception as e:
        logger.error(f"WebSocket error for {symbol}: {e}")
        manager.disconnect(websocket, symbol)
