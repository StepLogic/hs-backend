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

## Render Deployment

1. Create a new **Web Service** on Render and connect your repository.
2. Select **Python 3** as the environment.
3. Set the start command to:
   ```bash
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
   ```
4. Add a **PostgreSQL** database in the Render dashboard.
5. Copy the internal database URL and set it as the `DATABASE_URL` environment variable.
6. Set `SECRET_KEY` to a secure random string.
7. Deploy. After the first deploy, run migrations via Render Shell:
   ```bash
   alembic upgrade head
   ```

Or use the included `render.yaml` for blueprint-based deployment.

## API Documentation

Once running, view interactive docs at:

- Swagger UI: `/docs`
- ReDoc: `/redoc`
