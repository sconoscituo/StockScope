# StockScope - 프로젝트 설정 가이드

AI 기반 주식 매매 시그널 분석 및 관심 종목 포트폴리오 관리 서비스입니다.
FastAPI 백엔드 + SQLite + Telegram 알림으로 구성되어 있습니다.

---

## 1. 필요한 API 키 / 환경변수

| 환경변수 | 설명 | 발급 URL |
|---|---|---|
| `GEMINI_API_KEY` | 뉴스 분석 및 시장 분석 AI (Google Gemini) | https://aistudio.google.com/app/apikey |
| `SECRET_KEY` | JWT 서명 비밀키 | 직접 생성 (`openssl rand -hex 32`) |
| `TELEGRAM_BOT_TOKEN` | 매매 시그널 Telegram 알림 봇 토큰 | https://t.me/BotFather |
| `PORTONE_API_KEY` | 포트원 결제 API 키 | https://admin.portone.io |
| `PORTONE_API_SECRET` | 포트원 결제 API Secret | https://admin.portone.io |
| `DATABASE_URL` | DB 연결 URL (기본값: SQLite) | 직접 구성 (프로덕션은 PostgreSQL 권장) |

> `yfinance` 를 사용하므로 별도의 주식 데이터 API 키는 불필요합니다.

---

## 2. GitHub Secrets 설정

GitHub 레포지토리 > **Settings > Secrets and variables > Actions > New repository secret** 에서 아래 항목을 추가합니다.

```
GEMINI_API_KEY
SECRET_KEY
TELEGRAM_BOT_TOKEN
PORTONE_API_KEY
PORTONE_API_SECRET
DATABASE_URL
```

---

## 3. 로컬 개발 환경 설정

### 3-1. .env 파일 생성

프로젝트 루트에 `.env` 파일을 생성합니다:

```env
DATABASE_URL=sqlite+aiosqlite:///./stockscope.db
SECRET_KEY=your-secret-key-minimum-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
GEMINI_API_KEY=your_gemini_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
DEBUG=true
FREE_PLAN_STOCK_LIMIT=3
BUY_SIGNAL_NOTIFY_THRESHOLD=80
PORTONE_API_KEY=your_portone_api_key
PORTONE_API_SECRET=your_portone_api_secret
```

### 3-2. 의존성 설치

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## 4. 실행 방법

### 로컬 실행

```bash
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API 문서: http://localhost:8000/docs

헬스체크: http://localhost:8000/health

> 서버 시작 시 30분마다 관심 종목 시그널을 자동 업데이트하는 스케줄러가 실행됩니다.

---

## 5. 배포 방법

### Docker로 배포

```bash
docker build -t stockscope .
docker run -d -p 8000:8000 --env-file .env \
  -v $(pwd)/stockscope.db:/app/stockscope.db \
  stockscope
```

### Docker Compose로 배포

```bash
docker compose up --build -d
```

- API 서버: http://localhost:8000
- SQLite DB: `./stockscope.db` 에 볼륨 마운트됩니다.

### GitHub Actions 자동 배포

`.github/workflows/ci.yml` 을 통해 `main` 브랜치에 push 시 CI가 실행됩니다.
배포 전 위의 GitHub Secrets가 모두 설정되어 있어야 합니다.
