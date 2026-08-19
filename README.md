# HS Backend

Administration backend for the hs-platform homeschool assessment system.

## Setup

1. Clone the repository and navigate to the project directory.
2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and configure your environment variables.
5. Run Alembic migrations:
   ```bash
   alembic upgrade head
   ```
6. Start the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

## DigitalOcean App Platform Deployment

The backend is deployed on DigitalOcean App Platform (web service) backed by a DigitalOcean managed PostgreSQL database.

1. Create a **Web Service** on App Platform and connect this repository (autodeploys from `main`).
2. Set the run command to:
   ```bash
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
   ```
3. Set environment variables: `DATABASE_URL` (the managed Postgres connection string), `SECRET_KEY`, `FRONTEND_URL`, plus `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET` if auth is enabled.
4. The managed Postgres is behind **Trusted Sources** — the App Platform app's egress must be allowlisted there (it is, by default, for the app).
5. After each deploy that includes a new migration, run migrations from the App Platform **Console**:
   ```bash
   alembic upgrade head
   ```
   (Migrations are NOT run automatically on deploy.)

## API Documentation

Once running, view interactive docs at:

- Swagger UI: `/docs`
- ReDoc: `/redoc`
