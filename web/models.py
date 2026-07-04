from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import Optional


class Transaction(BaseModel):
    """
    Transaction model representing a single financial transaction.
    Matches the structure from the CLI analyzer.
    """
    date: str = Field(..., description="Transaction date in YYYY-MM-DD format")
    category: str = Field(..., description="Transaction category (e.g., food, gas, bills)")
    description: str = Field(..., description="Transaction description")
    amount: float = Field(..., gt=0, description="Transaction amount (must be positive)")
    
    @field_validator('date')
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate that date is in YYYY-MM-DD format."""
        try:
            parts = v.split('-')
            if len(parts) != 3:
                raise ValueError("Date must be in YYYY-MM-DD format")
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            date(year, month, day)
            return v
        except (ValueError, IndexError):
            raise ValueError(f"Invalid date format: {v}. Expected YYYY-MM-DD")
    
    @field_validator('category')
    @classmethod
    def validate_category(cls, v: str) -> str:
        """Ensure category is not empty."""
        if not v or not v.strip():
            raise ValueError("Category cannot be empty")
        return v.strip().lower()
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Ensure description is not empty."""
        if not v or not v.strip():
            raise ValueError("Description cannot be empty")
        return v.strip()
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: float) -> float:
        """Ensure amount is positive and has reasonable precision."""
        if v <= 0:
            raise ValueError("Amount must be positive")
        return round(v, 2)


class Expense(BaseModel):
    description: str
    amount: float
    category: str


class ExpenseUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[float] = None
    category: Optional[str] = None
