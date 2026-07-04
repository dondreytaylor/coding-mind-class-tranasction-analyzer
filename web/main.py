from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import ValidationError
from typing import Optional, List
from sqlalchemy.orm import Session
import csv
import io
import os
from models import Transaction, Expense, ExpenseUpdate

try:
    from database import get_db, TransactionDB, init_db
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    print("Database module not available. Install sqlalchemy and psycopg2-binary to enable Postgres support.")

app = FastAPI(title="Expense Tracker API")

# Mount static files (css, js, images)
app.mount("/static", StaticFiles(directory="static"), name="static")


# -------------------------------------------------------------------
# In-memory store (replace with a real DB in production)
# -------------------------------------------------------------------

expenses: dict[int, dict] = {}
next_id: int = 1


# -------------------------------------------------------------------
# Page routes
# -------------------------------------------------------------------

@app.get("/", response_class=FileResponse)
async def landing_page():
    """Serve the HTML landing page."""
    return FileResponse(os.path.join("templates", "index.html"))


# -------------------------------------------------------------------
# API routes — Expenses
# -------------------------------------------------------------------

@app.get("/api/expenses", summary="Get all expenses")
async def get_expenses():
    """Return every expense in the store."""
    return {"expenses": list(expenses.values())}


@app.get("/api/expenses/{expense_id}", summary="Get a single expense")
async def get_expense(expense_id: int):
    """Return a single expense by ID."""
    if expense_id not in expenses:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expenses[expense_id]


@app.post("/api/expenses", status_code=201, summary="Create a new expense")
async def create_expense(expense: Expense):
    """Create a new expense and return it with its assigned ID."""
    global next_id
    record = {"id": next_id, **expense.model_dump()}
    expenses[next_id] = record
    next_id += 1
    return record

@app.put("/api/expenses/{expense_id}", summary="Update an existing expense")
async def update_expense(expense_id: int, updates: ExpenseUpdate):
    """Partially update an existing expense by ID."""
    if expense_id not in expenses:
        raise HTTPException(status_code=404, detail="Expense not found")
    record = expenses[expense_id]
    patch = updates.model_dump(exclude_unset=True)
    record.update(patch)
    return record


# -------------------------------------------------------------------
# API routes — CSV Upload
# -------------------------------------------------------------------

@app.post("/api/upload-csv", summary="Upload a CSV of transactions")
async def upload_csv(file: UploadFile = File(...)):
    """
    Accept a CSV file upload, validate structure and data types,
    parse rows into Transaction objects, and return validation results.
    
    Expected CSV columns: date, category, description, amount
    """
    filename = file.filename or ""
    if not filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted")

    content = await file.read()

    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File exceeds the 5 MB limit")

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded")

    reader = csv.DictReader(io.StringIO(text))

    if reader.fieldnames is None:
        raise HTTPException(status_code=400, detail="CSV file appears to be empty")

    # Validate required columns
    required_columns = {"date", "category", "description", "amount"}
    actual_columns = {col.strip().lower() for col in reader.fieldnames if col}
    
    missing_columns = required_columns - actual_columns
    if missing_columns:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {', '.join(sorted(missing_columns))}. Expected: date, category, description, amount"
        )

    # Parse and validate transactions
    valid_transactions = []
    invalid_rows = []
    row_number = 1
    
    for row in reader:
        row_number += 1
        try:
            # Normalize column names and strip whitespace
            normalized_row = {k.strip().lower(): v.strip() for k, v in row.items() if k}
            
            # Convert amount to float
            try:
                normalized_row['amount'] = float(normalized_row['amount'])
            except (ValueError, KeyError) as e:
                raise ValueError(f"Invalid amount value: {normalized_row.get('amount', 'missing')}")
            
            # Validate using Transaction model
            transaction = Transaction(**normalized_row)
            valid_transactions.append(transaction.model_dump())
            
        except (ValidationError, ValueError) as e:
            error_msg = str(e)
            if isinstance(e, ValidationError):
                errors = e.errors()
                error_msg = "; ".join([f"{err['loc'][0]}: {err['msg']}" for err in errors])
            
            invalid_rows.append({
                "row": row_number,
                "data": {k.strip(): v.strip() for k, v in row.items() if k},
                "errors": error_msg
            })

    # Calculate summary statistics
    total_amount = sum(t['amount'] for t in valid_transactions)
    category_totals = {}
    for t in valid_transactions:
        cat = t['category']
        category_totals[cat] = category_totals.get(cat, 0) + t['amount']

    is_valid = len(invalid_rows) == 0
    
    return {
        "filename": filename,
        "is_valid": is_valid,
        "total_rows": row_number - 1,
        "valid_rows": len(valid_transactions),
        "invalid_rows": len(invalid_rows),
        "total_amount": round(total_amount, 2),
        "category_breakdown": {k: round(v, 2) for k, v in category_totals.items()},
        "transactions": valid_transactions,
        "errors": invalid_rows if invalid_rows else None,
        "message": "All transactions validated successfully!" if is_valid else f"Found {len(invalid_rows)} invalid row(s)"
    }


# -------------------------------------------------------------------
# API routes — Postgres Database (Optional)
# -------------------------------------------------------------------

if DB_AVAILABLE:
    @app.on_event("startup")
    async def startup_event():
        """Initialize database tables on startup."""
        try:
            init_db()
            print("Database initialized successfully!")
        except Exception as e:
            print(f"Warning: Could not initialize database: {e}")
            print("Database features will be unavailable.")
    
    @app.post("/api/db/transactions", summary="Save transactions to Postgres database")
    async def save_transactions_to_db(
        transactions: List[Transaction],
        db: Session = Depends(get_db)
    ):
        """
        Save a list of validated transactions to the Postgres database.
        Accepts an array of Transaction objects.
        """
        try:
            saved_count = 0
            for transaction in transactions:
                db_transaction = TransactionDB(
                    date=transaction.date,
                    category=transaction.category,
                    description=transaction.description,
                    amount=transaction.amount
                )
                db.add(db_transaction)
                saved_count += 1
            
            db.commit()
            
            return {
                "success": True,
                "saved_count": saved_count,
                "message": f"Successfully saved {saved_count} transaction(s) to database"
            }
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    @app.get("/api/db/transactions", summary="Get all transactions from Postgres database")
    async def get_transactions_from_db(
        category: Optional[str] = None,
        limit: int = 100,
        db: Session = Depends(get_db)
    ):
        """
        Retrieve transactions from the Postgres database.
        Optionally filter by category and limit results.
        """
        try:
            query = db.query(TransactionDB)
            
            if category:
                query = query.filter(TransactionDB.category == category.lower())
            
            transactions = query.order_by(TransactionDB.date.desc()).limit(limit).all()
            
            return {
                "count": len(transactions),
                "transactions": [
                    {
                        "id": t.id,
                        "date": t.date,
                        "category": t.category,
                        "description": t.description,
                        "amount": t.amount,
                        "created_at": t.created_at
                    }
                    for t in transactions
                ]
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    @app.get("/api/db/stats", summary="Get transaction statistics from database")
    async def get_transaction_stats(db: Session = Depends(get_db)):
        """
        Get aggregated statistics from all transactions in the database.
        """
        try:
            transactions = db.query(TransactionDB).all()
            
            if not transactions:
                return {
                    "total_transactions": 0,
                    "total_amount": 0,
                    "category_breakdown": {}
                }
            
            total_amount = sum(t.amount for t in transactions)
            category_totals = {}
            
            for t in transactions:
                category_totals[t.category] = category_totals.get(t.category, 0) + t.amount
            
            return {
                "total_transactions": len(transactions),
                "total_amount": round(total_amount, 2),
                "category_breakdown": {k: round(v, 2) for k, v in category_totals.items()},
                "categories": list(category_totals.keys())
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

