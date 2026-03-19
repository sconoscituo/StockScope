# StockScope

한국/미국 주식 AI 분석 도구. 실시간 주가 데이터 수집 + Gemini AI 매수/매도 시그널 + 경제 뉴스 감성 분석 + 텔레그램 알림.

## 주요 기능

- **AI 시그널 생성**: Gemini AI가 RSI, 이동평균, 뉴스 감성을 종합하여 BUY/SELL/HOLD 시그널 생성
- **실시간 주가 수집**: yfinance로 한국(코스피/코스닥) + 미국 주식 데이터 수집
- **뉴스 감성 분석**: 연합뉴스, 한국경제, Bloomberg RSS 파싱 → 공포/탐욕 지수 산출
- **텔레그램 알림**: BUY 시그널 80점 이상 시 자동 알림 (프리미엄 전용)
- **자동 스케줄링**: 30분마다 전체 관심 종목 시그널 자동 갱신

## 수익 구조

| 플랜 | 종목 수 | 실시간 알림 | 가격 |
|------|---------|------------|------|
| 무료 | 최대 3개 | X | 무료 |
| 프리미엄 | 무제한 | O (텔레그램) | 월 9,900원 |

## 기술 스택

- **Backend**: FastAPI, SQLAlchemy (async), SQLite
- **AI**: Google Gemini API (gemini-1.5-flash)
- **주가 데이터**: yfinance, FinanceDataReader
- **스케줄러**: APScheduler
- **알림**: python-telegram-bot
- **인증**: JWT (python-jose)

## 설치 및 실행

### 로컬 실행

```bash
# 1. 저장소 클론
git clone https://github.com/sconoscituo/StockScope.git
cd StockScope

# 2. 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 환경변수 설정
cp .env.example .env
# .env 파일에 API 키 입력

# 5. 서버 실행
uvicorn app.main:app --reload
```

### Docker 실행

```bash
cp .env.example .env
# .env 파일 편집

docker-compose up -d
```

서버 실행 후 http://localhost:8000/docs 에서 Swagger UI 확인

## 환경변수

| 변수 | 설명 | 필수 |
|------|------|------|
| `GEMINI_API_KEY` | Google Gemini API 키 | O |
| `SECRET_KEY` | JWT 서명 비밀키 | O |
| `DATABASE_URL` | SQLite DB 경로 | O |
| `TELEGRAM_BOT_TOKEN` | 텔레그램 봇 토큰 | 선택 |
| `DEBUG` | 디버그 모드 | 선택 |

## 주요 API

### 인증

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/users/register` | 회원가입 |
| POST | `/api/users/login` | 로그인 (JWT 발급) |
| GET | `/api/users/me` | 내 정보 조회 |
| PATCH | `/api/users/me` | 텔레그램 chat_id 등록 |
| POST | `/api/users/upgrade` | 플랜 업그레이드 |

### 종목 관리

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/stocks` | 관심 종목 추가 |
| GET | `/api/stocks` | 관심 종목 목록 |
| DELETE | `/api/stocks/{id}` | 종목 삭제 |
| GET | `/api/stocks/{ticker}/signals` | 시그널 이력 조회 |
| POST | `/api/stocks/{ticker}/refresh` | 시그널 즉시 갱신 |

### 시장 분석

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/analysis` | 분석 이력 목록 |
| GET | `/api/analysis/latest` | 최신 시장 분석 |
| POST | `/api/analysis/run` | 시장 분석 즉시 실행 |

## 종목 티커 형식

- **한국 주식**: 6자리 코드 입력 (예: `005930` → 내부적으로 `005930.KS` 변환)
- **미국 주식**: 그대로 입력 (예: `AAPL`, `MSFT`, `TSLA`)

## 시그널 예시

```json
{
  "ticker": "AAPL",
  "action": "BUY",
  "score": 82.5,
  "reason": "RSI 28.3으로 과매도 구간 진입. 5일 이동평균이 반등 조짐을 보이며 뉴스 감성 점수 긍정적.",
  "current_price": 182.50,
  "price_change_5d": -3.2,
  "rsi": 28.3,
  "news_sentiment": 0.15
}
```

## 테스트

```bash
pytest tests/ -v --asyncio-mode=auto
```

## 라이선스

MIT
