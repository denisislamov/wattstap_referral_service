# WattsTap Referral Service

Backend service for handling the referral system in WattsTap Telegram Mini App.

## Features

- **Telegram Authentication**: Secure authentication using Telegram WebApp initData
- **Referral System**: Invite friends via referral links and earn bonus watts
- **Friends List**: Track your friends and referral statistics

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy (async)
- **Migrations**: Alembic
- **Authentication**: JWT tokens
- **Python**: 3.11+

## Project Structure

```
wattstap-referral-service/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration from environment
│   ├── database.py          # Database setup and session
│   ├── dependencies.py      # FastAPI dependencies (auth)
│   │
│   ├── models/              # SQLAlchemy models
│   │   ├── user.py          # User model
│   │   └── friendship.py    # Friendship model
│   │
│   ├── schemas/             # Pydantic schemas
│   │   ├── auth.py          # Auth request/response schemas
│   │   ├── social.py        # Social features schemas
│   │   └── common.py        # Common schemas
│   │
│   ├── services/            # Business logic
│   │   ├── telegram_auth.py # Telegram initData validation
│   │   ├── user_service.py  # User management
│   │   └── referral_service.py # Referral logic
│   │
│   └── routers/             # API endpoints
│       ├── auth.py          # /auth/* endpoints
│       └── social.py        # /social/* endpoints
│
├── alembic/                 # Database migrations
├── tests/                   # Test files
├── requirements.txt
├── alembic.ini
└── README.md
```

## Setup

### 1. Create Virtual Environment

```bash
cd wattstap-referral-service
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/wattstap_referral

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_BOT_USERNAME=WattsTapBot

# JWT
JWT_SECRET=your-super-secret-key-here
```

### 4. Setup Database

Create the database:

```bash
createdb wattstap_referral
```

Run migrations:

```bash
alembic upgrade head
```

### 5. Run the Server

Development mode:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or using Python:

```bash
python -m app.main
```

## API Endpoints

### Authentication

#### POST /auth/telegram

Authenticate using Telegram WebApp initData.

**Request:**
```json
{
  "initData": "query_id=...&user=...&auth_date=...&hash=...",
  "referralCode": "ABC123"  // optional
}
```

**Response:**
```json
{
  "token": "eyJ...",
  "expiresIn": 86400,
  "player": {
    "playerId": "1",
    "nickname": "Username",
    "level": 1,
    "isNewPlayer": true,
    "referralCode": "XYZ789"
  },
  "referral": {
    "applied": true,
    "referrer": {
      "userId": 123456789,
      "nickname": "Friend",
      "level": 5
    },
    "bonusForReferrer": 5000,
    "message": "You were invited by Friend!"
  }
}
```

### Social

#### GET /social/my-referral

Get your referral code and statistics. Requires authentication.

**Response:**
```json
{
  "referralCode": "ABC123",
  "inviteLink": "https://t.me/WattsTapBot?start=REF_ABC123",
  "bonusPerFriend": 5000,
  "totalFriendsInvited": 10,
  "totalBonusEarned": 50000
}
```

#### GET /social/friends

Get your friends list. Requires authentication.

**Response:**
```json
{
  "friends": [
    {
      "playerId": "2",
      "nickname": "Friend1",
      "level": 3,
      "avatarUrl": "https://...",
      "totalEarnings": 15000,
      "yourBonus": 5000,
      "invitedAt": "2024-12-01T10:00:00Z"
    }
  ],
  "totalFriends": 1,
  "totalBonusEarned": 5000
}
```

## How Referral System Works

1. **User A** shares their referral link: `https://t.me/WattsTapBot?start=REF_ABC123`

2. **User B** clicks the link and opens the Mini App

3. Telegram includes `start_param=REF_ABC123` in the initData

4. When **User B** authenticates:
   - The referral code is validated
   - **User B** is created with `referred_by` pointing to **User A**
   - A mutual friendship is created
   - **User A** receives 5000 watts bonus

5. Referral codes only work for new users (first login)

## Development

### Run Tests

```bash
pytest
```

### Create New Migration

```bash
alembic revision --autogenerate -m "description"
```

### Apply Migrations

```bash
alembic upgrade head
```

### Rollback Migration

```bash
alembic downgrade -1
```

## Docker (Optional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t wattstap-referral .
docker run -p 8000:8000 --env-file .env wattstap-referral
```

## License

Proprietary - WattsTap


