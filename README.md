# PhishShield

PhishShield — AI-Driven Phishing Email & Malicious Attachment Sandboxing Portal.

## Backend Development Setup

### Prerequisites
- Python 3.10+
- PostgreSQL
- Redis

### Setup Instructions

1. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configuration:**
   Copy `.env.example` to `.env` and adjust the variables as needed.
   ```bash
   cp .env.example .env
   ```

4. **Database Migrations:**
   Run Alembic migrations to set up the database schema:
   ```bash
   alembic upgrade head
   ```

5. **Run the Development Server:**
   ```bash
   uvicorn app.main:app --reload
   ```

6. **Run Celery Worker:**
   ```bash
   celery -A app.core.celery_app worker --loglevel=info
   ```

### Testing
Run tests using pytest:
```bash
pytest
```
