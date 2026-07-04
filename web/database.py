from sqlalchemy import create_engine, Column, Integer, String, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Database URL - can be configured via environment variable
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://localhost:5432/expense_tracker"
)

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=True)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


class TransactionDB(Base):
    """
    SQLAlchemy model for storing transactions in Postgres.
    """
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    date = Column(String, nullable=False, index=True)
    category = Column(String, nullable=False, index=True)
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    created_at = Column(String, default=lambda: datetime.utcnow().isoformat())
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, date={self.date}, category={self.category}, amount={self.amount})>"


def init_db():
    """
    Initialize the database by creating all tables.
    Call this function once to set up the database schema.
    """
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


def get_db():
    """
    Dependency function to get database session.
    Use this in FastAPI endpoints with Depends().
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
