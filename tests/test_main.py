import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.database import Base, get_db

# 테스트용 인메모리 SQLite DB
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_root(client):
    resp = await client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["service"] == "StockScope"


@pytest.mark.asyncio
async def test_register_and_login(client):
    # 회원가입
    resp = await client.post(
        "/api/users/register",
        json={"email": "test@example.com", "password": "testpass123"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "test@example.com"
    assert data["plan"] == "free"

    # 로그인
    resp = await client.post(
        "/api/users/login",
        data={"username": "test@example.com", "password": "testpass123"},
    )
    assert resp.status_code == 200
    token_data = resp.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_duplicate_register(client):
    await client.post(
        "/api/users/register",
        json={"email": "dup@example.com", "password": "pass"},
    )
    resp = await client.post(
        "/api/users/register",
        json={"email": "dup@example.com", "password": "pass"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_add_stock_free_limit(client):
    # 회원가입 및 로그인
    await client.post(
        "/api/users/register",
        json={"email": "user@example.com", "password": "pass123"},
    )
    login_resp = await client.post(
        "/api/users/login",
        data={"username": "user@example.com", "password": "pass123"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3개 종목 추가 (무료 한도)
    tickers = [
        ("AAPL", "Apple Inc.", "US"),
        ("MSFT", "Microsoft", "US"),
        ("GOOGL", "Alphabet", "US"),
    ]
    for ticker, name, market in tickers:
        resp = await client.post(
            "/api/stocks",
            json={"ticker": ticker, "name": name, "market": market},
            headers=headers,
        )
        assert resp.status_code == 201

    # 4번째 종목 추가 시 403
    resp = await client.post(
        "/api/stocks",
        json={"ticker": "TSLA", "name": "Tesla", "market": "US"},
        headers=headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_get_me(client):
    await client.post(
        "/api/users/register",
        json={"email": "me@example.com", "password": "pass"},
    )
    login_resp = await client.post(
        "/api/users/login",
        data={"username": "me@example.com", "password": "pass"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.get("/api/users/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"


@pytest.mark.asyncio
async def test_unauthorized_access(client):
    resp = await client.get("/api/stocks")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_price_fetcher_rsi():
    from app.services.price_fetcher import calculate_rsi

    # RSI 계산 검증 (데이터 부족)
    assert calculate_rsi([100, 101, 102], period=14) is None

    # 충분한 데이터로 RSI 계산
    prices = [float(i) for i in range(1, 25)]
    rsi = calculate_rsi(prices, period=14)
    assert rsi is not None
    assert 0 <= rsi <= 100


@pytest.mark.asyncio
async def test_moving_averages():
    from app.services.price_fetcher import get_moving_averages

    prices = [float(i) for i in range(1, 26)]
    ma = get_moving_averages(prices)
    assert ma["ma5"] is not None
    assert ma["ma20"] is not None
    assert ma["ma5"] == pytest.approx(sum(prices[-5:]) / 5, rel=1e-3)
