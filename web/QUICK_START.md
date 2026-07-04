# Quick Start Guide

## Test the Enhanced Expense Tracker (Without Installing Dependencies)

### Option 1: Test Validation Logic Only

Run the validation test script (no server required):

```bash
cd web
python3 test_validation.py
```

Expected output:
```
============================================================
Transaction Model Validation Tests
============================================================
Testing valid transaction...
✓ Valid transaction created: {...}

Testing invalid date...
✓ Correctly rejected invalid date: ...

Testing negative amount...
✓ Correctly rejected negative amount: ...

Testing empty category...
✓ Correctly rejected empty category: ...

Testing missing field...
✓ Correctly rejected missing field: ...

Testing category normalization...
✓ Category normalized: 'FOOD' -> 'food'

Testing amount rounding...
✓ Amount rounded: 10.999 -> 11.0

============================================================
Results: 7/7 tests passed
============================================================
✓ All validation tests passed!
```

---

## Full Server Setup (With Dependencies)

### Step 1: Create Virtual Environment

```bash
cd web
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- FastAPI
- Uvicorn
- Python-multipart
- SQLAlchemy (for database)
- psycopg2-binary (for PostgreSQL)

### Step 3: Start the Server

```bash
uvicorn main:app --reload
```

Expected output:
```
INFO:     Will watch for changes in these directories: ['/path/to/web']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
Database module not available. Install sqlalchemy and psycopg2-binary to enable Postgres support.
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

Note: The "Database module not available" message is normal if you haven't set up PostgreSQL yet.

### Step 4: Test the API

#### Open the interactive docs:
Visit `http://localhost:8000/docs` in your browser

#### Or use curl:

**Test CSV upload with the sample file:**
```bash
curl -X POST "http://localhost:8000/api/upload-csv" \
  -F "file=@../cli/transactions.csv"
```

**Expected response:**
```json
{
  "filename": "transactions.csv",
  "is_valid": true,
  "total_rows": 8,
  "valid_rows": 8,
  "invalid_rows": 0,
  "total_amount": 374.54,
  "category_breakdown": {
    "food": 41.0,
    "gas": 83.2,
    "shopping": 170.34,
    "bills": 80.0
  },
  "transactions": [
    {
      "date": "2026-06-01",
      "category": "food",
      "description": "lunch",
      "amount": 12.5
    },
    ...
  ],
  "errors": null,
  "message": "All transactions validated successfully!"
}
```

---

## Test Invalid Data

Create a test file with errors:

```bash
cat > test_invalid.csv << 'EOF'
date,category,description,amount
2026-07-01,food,lunch,12.50
2026-13-45,food,invalid date,10.00
2026-07-02,gas,gas,-50.00
invalid-date,shopping,bad date,25.00
2026-07-03,,empty category,15.00
EOF
```

Upload it:
```bash
curl -X POST "http://localhost:8000/api/upload-csv" \
  -F "file=@test_invalid.csv"
```

**Expected response:**
```json
{
  "filename": "test_invalid.csv",
  "is_valid": false,
  "total_rows": 5,
  "valid_rows": 1,
  "invalid_rows": 4,
  "total_amount": 12.5,
  "category_breakdown": {
    "food": 12.5
  },
  "transactions": [
    {
      "date": "2026-07-01",
      "category": "food",
      "description": "lunch",
      "amount": 12.5
    }
  ],
  "errors": [
    {
      "row": 3,
      "data": {"date": "2026-13-45", "category": "food", "description": "invalid date", "amount": "10.00"},
      "errors": "date: Invalid date format: 2026-13-45. Expected YYYY-MM-DD"
    },
    {
      "row": 4,
      "data": {"date": "2026-07-02", "category": "gas", "description": "gas", "amount": "-50.00"},
      "errors": "amount: Amount must be positive"
    },
    ...
  ],
  "message": "Found 4 invalid row(s)"
}
```

---

## Optional: Set Up PostgreSQL

If you want to test database features:

### 1. Install PostgreSQL

**macOS:**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### 2. Create Database

```bash
psql postgres -c "CREATE DATABASE expense_tracker;"
```

### 3. Set Environment Variable

```bash
export DATABASE_URL="postgresql://localhost:5432/expense_tracker"
```

### 4. Restart Server

```bash
uvicorn main:app --reload
```

Now you should see:
```
Database initialized successfully!
Database tables created successfully!
```

### 5. Test Database Endpoints

**Save transactions:**
```bash
curl -X POST "http://localhost:8000/api/db/transactions" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "date": "2026-07-04",
      "category": "food",
      "description": "Lunch",
      "amount": 15.50
    },
    {
      "date": "2026-07-04",
      "category": "gas",
      "description": "Gas station",
      "amount": 45.00
    }
  ]'
```

**Get all transactions:**
```bash
curl "http://localhost:8000/api/db/transactions"
```

**Get statistics:**
```bash
curl "http://localhost:8000/api/db/stats"
```

**Filter by category:**
```bash
curl "http://localhost:8000/api/db/transactions?category=food&limit=10"
```

---

## Troubleshooting

### "Module not found" errors
Make sure you're in the virtual environment:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "Port already in use"
Change the port:
```bash
uvicorn main:app --reload --port 8001
```

### Database connection errors
Check PostgreSQL is running:
```bash
brew services list  # macOS
sudo systemctl status postgresql  # Linux
```

Verify database exists:
```bash
psql postgres -c "\l" | grep expense_tracker
```

### CSV upload fails
Check file format:
- Must have `.csv` extension
- Must be UTF-8 encoded
- Must have header row: `date,category,description,amount`
- Maximum size: 5 MB

---

## What's Been Enhanced

✅ **CSV Validation:**
- Required columns check
- Data type validation
- Business rule validation (dates, amounts)
- Per-row error reporting

✅ **Transaction Model:**
- Pydantic validation
- Automatic type conversion
- Category normalization
- Amount rounding

✅ **Enhanced Response:**
- Validation status flag
- Summary statistics
- Category breakdown
- Detailed error messages

✅ **Database Integration (Optional):**
- PostgreSQL support
- Save/query transactions
- Aggregated statistics
- Category filtering

---

## Next Steps

1. **Review the code:**
   - `models.py` - Transaction validation logic
   - `main.py` - Enhanced upload_csv function
   - `database.py` - PostgreSQL integration

2. **Read the documentation:**
   - `IMPLEMENTATION_SUMMARY.md` - Complete overview
   - `DATABASE_SETUP.md` - Database setup guide
   - `CHANGES.md` - Detailed change log

3. **Test the features:**
   - Upload valid CSV files
   - Test with invalid data
   - Try database endpoints (if configured)

4. **Extend the functionality:**
   - Add frontend validation display
   - Implement data visualization
   - Add user authentication
   - Create export features

---

## API Endpoints Summary

### Existing Endpoints (Unchanged)
- `GET /` - Landing page
- `GET /api/expenses` - Get all expenses
- `POST /api/expenses` - Create expense
- `PUT /api/expenses/{id}` - Update expense

### Enhanced Endpoint
- `POST /api/upload-csv` - Upload and validate CSV (now with detailed validation)

### New Database Endpoints (Optional)
- `POST /api/db/transactions` - Save transactions to database
- `GET /api/db/transactions` - Query transactions
- `GET /api/db/stats` - Get aggregated statistics

Visit `http://localhost:8000/docs` for interactive API documentation!
