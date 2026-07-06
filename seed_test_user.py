"""Seed a test user for development."""

from app.database import SessionLocal, engine
from app.models import Base, User
from app.security import hash_password

def create_test_user():
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if user already exists
        existing = db.query(User).filter(User.email == "test@test.com").first()
        if existing:
            print("Test user already exists!")
            return

        # Create test user
        user = User(
            email="test@test.com",
            name="Test User",
            password_hash=hash_password("Test123!"),
            role="student"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Created test user: {user.email}")
        print("Login with:")
        print("  Email: test@test.com")
        print("  Password: Test123!")
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()
