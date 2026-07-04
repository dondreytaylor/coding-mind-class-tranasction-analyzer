from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import csv
import io
import os

app = FastAPI(title="Expense Tracker API")

# Mount static files (css, js, images)
app.mount("/static", StaticFiles(directory="static"), name="static")


# -------------------------------------------------------------------
# Models
# -------------------------------------------------------------------

class Expense(BaseModel):
    description: str
    amount: float
    category: str


class ExpenseUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[float] = None
    category: Optional[str] = None


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
    Accept a CSV file upload, parse every row, and return the
    rows as a JSON array.  The first row is treated as a header.
    Accepts files with a .csv extension and text/csv MIME type.
    """
    # Validate file type
    filename = file.filename or ""
    if not filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted")

    content = await file.read()

    # Limit file size to 5 MB to prevent DoS via huge uploads
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File exceeds the 5 MB limit")

    try:
        text = content.decode("utf-8-sig")  # utf-8-sig strips BOM if present
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded")

    reader = csv.DictReader(io.StringIO(text))

    if reader.fieldnames is None:
        raise HTTPException(status_code=400, detail="CSV file appears to be empty")

    rows = []
    for row in reader:
        # Strip whitespace from keys and values
        rows.append({k.strip(): v.strip() for k, v in row.items() if k})

    return {
        "filename": filename,
        "rows": len(rows),
        "columns": [f.strip() for f in reader.fieldnames],
        "data": rows,
    }

