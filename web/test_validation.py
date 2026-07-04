#!/usr/bin/env python3
"""
Quick test script to verify Transaction model validation works correctly.
This tests the validation logic without needing to run the full server.
"""

from models import Transaction
from pydantic import ValidationError

def test_valid_transaction():
    """Test that valid transactions pass validation."""
    print("Testing valid transaction...")
    try:
        t = Transaction(
            date="2026-07-04",
            category="food",
            description="Lunch at cafe",
            amount=15.50
        )
        print(f"✓ Valid transaction created: {t.model_dump()}")
        return True
    except ValidationError as e:
        print(f"✗ Unexpected validation error: {e}")
        return False

def test_invalid_date():
    """Test that invalid dates are rejected."""
    print("\nTesting invalid date...")
    try:
        t = Transaction(
            date="2026-13-45",  # Invalid month and day
            category="food",
            description="Test",
            amount=10.00
        )
        print(f"✗ Should have failed but got: {t.model_dump()}")
        return False
    except ValidationError as e:
        print(f"✓ Correctly rejected invalid date: {e.errors()[0]['msg']}")
        return True

def test_negative_amount():
    """Test that negative amounts are rejected."""
    print("\nTesting negative amount...")
    try:
        t = Transaction(
            date="2026-07-04",
            category="food",
            description="Test",
            amount=-10.00
        )
        print(f"✗ Should have failed but got: {t.model_dump()}")
        return False
    except ValidationError as e:
        print(f"✓ Correctly rejected negative amount: {e.errors()[0]['msg']}")
        return True

def test_empty_category():
    """Test that empty categories are rejected."""
    print("\nTesting empty category...")
    try:
        t = Transaction(
            date="2026-07-04",
            category="",
            description="Test",
            amount=10.00
        )
        print(f"✗ Should have failed but got: {t.model_dump()}")
        return False
    except ValidationError as e:
        print(f"✓ Correctly rejected empty category: {e.errors()[0]['msg']}")
        return True

def test_missing_field():
    """Test that missing required fields are rejected."""
    print("\nTesting missing field...")
    try:
        t = Transaction(
            date="2026-07-04",
            category="food",
            description="Test"
            # Missing amount
        )
        print(f"✗ Should have failed but got: {t.model_dump()}")
        return False
    except ValidationError as e:
        print(f"✓ Correctly rejected missing field: {e.errors()[0]['msg']}")
        return True

def test_category_normalization():
    """Test that categories are normalized to lowercase."""
    print("\nTesting category normalization...")
    try:
        t = Transaction(
            date="2026-07-04",
            category="FOOD",
            description="Test",
            amount=10.00
        )
        if t.category == "food":
            print(f"✓ Category normalized: 'FOOD' -> '{t.category}'")
            return True
        else:
            print(f"✗ Category not normalized: got '{t.category}'")
            return False
    except ValidationError as e:
        print(f"✗ Unexpected validation error: {e}")
        return False

def test_amount_rounding():
    """Test that amounts are rounded to 2 decimals."""
    print("\nTesting amount rounding...")
    try:
        t = Transaction(
            date="2026-07-04",
            category="food",
            description="Test",
            amount=10.999
        )
        if t.amount == 11.00:
            print(f"✓ Amount rounded: 10.999 -> {t.amount}")
            return True
        else:
            print(f"✗ Amount not rounded correctly: got {t.amount}")
            return False
    except ValidationError as e:
        print(f"✗ Unexpected validation error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Transaction Model Validation Tests")
    print("=" * 60)
    
    tests = [
        test_valid_transaction,
        test_invalid_date,
        test_negative_amount,
        test_empty_category,
        test_missing_field,
        test_category_normalization,
        test_amount_rounding
    ]
    
    results = [test() for test in tests]
    
    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
    
    if all(results):
        print("✓ All validation tests passed!")
        exit(0)
    else:
        print("✗ Some tests failed")
        exit(1)
