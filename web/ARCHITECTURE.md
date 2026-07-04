# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Browser    │  │     curl     │  │  API Client  │          │
│  │  (index.html)│  │   (CLI)      │  │  (External)  │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                   │
└─────────┼──────────────────┼──────────────────┼──────────────────┘
          │                  │                  │
          └──────────────────┴──────────────────┘
                             │
                    HTTP/JSON Requests
                             │
┌────────────────────────────▼─────────────────────────────────────┐
│                      FastAPI Application                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                      main.py                               │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │              API Route Handlers                      │  │  │
│  │  │  • GET /                    (Landing page)           │  │  │
│  │  │  • POST /api/upload-csv     (CSV validation)         │  │  │
│  │  │  • GET/POST /api/expenses   (In-memory CRUD)         │  │  │
│  │  │  • POST /api/db/transactions (Save to DB)            │  │  │
│  │  │  • GET /api/db/transactions  (Query DB)              │  │  │
│  │  │  • GET /api/db/stats         (Aggregated stats)      │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                             │                                     │
│         ┌───────────────────┼───────────────────┐                │
│         │                   │                   │                │
│         ▼                   ▼                   ▼                │
│  ┌─────────────┐   ┌──────────────┐   ┌──────────────┐         │
│  │  models.py  │   │ database.py  │   │ In-Memory    │         │
│  │             │   │              │   │ Storage      │         │
│  │ Transaction │   │ TransactionDB│   │ (expenses)   │         │
│  │ Expense     │   │ get_db()     │   │              │         │
│  │ Validation  │   │ init_db()    │   │              │         │
│  └─────────────┘   └──────┬───────┘   └──────────────┘         │
│                            │                                     │
└────────────────────────────┼─────────────────────────────────────┘
                             │
                    SQLAlchemy ORM
                             │
┌────────────────────────────▼─────────────────────────────────────┐
│                   PostgreSQL Database (Optional)                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    transactions table                      │  │
│  │  ┌──────┬──────────┬──────────┬─────────────┬────────┐   │  │
│  │  │  id  │   date   │ category │ description │ amount │   │  │
│  │  ├──────┼──────────┼──────────┼─────────────┼────────┤   │  │
│  │  │  1   │2026-07-01│   food   │   Lunch     │  15.50 │   │  │
│  │  │  2   │2026-07-02│   gas    │   Shell     │  45.00 │   │  │
│  │  │  3   │2026-07-03│ shopping │   Target    │  67.89 │   │  │
│  │  └──────┴──────────┴──────────┴─────────────┴────────┘   │  │
│  └───────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Data Flow: CSV Upload & Validation

```
┌─────────────┐
│   Client    │
│ (Browser)   │
└──────┬──────┘
       │
       │ 1. Upload CSV file
       │    POST /api/upload-csv
       ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI: upload_csv()                       │
│                                                          │
│  Step 1: File Validation                                │
│  ┌────────────────────────────────────────────────┐    │
│  │ • Check .csv extension                          │    │
│  │ • Verify file size (< 5 MB)                     │    │
│  │ • Validate UTF-8 encoding                       │    │
│  └────────────────────────────────────────────────┘    │
│                      │                                   │
│  Step 2: Column Validation                              │
│  ┌────────────────────────────────────────────────┐    │
│  │ • Parse CSV headers                             │    │
│  │ • Check required columns exist:                 │    │
│  │   - date, category, description, amount         │    │
│  └────────────────────────────────────────────────┘    │
│                      │                                   │
│  Step 3: Row-by-Row Validation                          │
│  ┌────────────────────────────────────────────────┐    │
│  │ For each row:                                   │    │
│  │   1. Normalize column names (lowercase)         │    │
│  │   2. Strip whitespace                           │    │
│  │   3. Convert amount to float                    │    │
│  │   4. Create Transaction object ──────┐         │    │
│  └──────────────────────────────────────┼─────────┘    │
│                                          │               │
│                                          ▼               │
│                              ┌────────────────────┐     │
│                              │   models.py        │     │
│                              │   Transaction      │     │
│                              │   Validation       │     │
│                              │                    │     │
│                              │ • Date format      │     │
│                              │ • Category valid   │     │
│                              │ • Amount positive  │     │
│                              │ • Description ok   │     │
│                              └────────┬───────────┘     │
│                                       │                 │
│                        ┌──────────────┴─────────────┐  │
│                        │                            │  │
│                   Valid ✓                      Invalid ✗│
│                        │                            │  │
│                        ▼                            ▼  │
│            ┌─────────────────────┐    ┌──────────────────┐
│            │ valid_transactions  │    │  invalid_rows    │
│            │ [Transaction, ...]  │    │  [{row, errors}] │
│            └──────────┬──────────┘    └────────┬─────────┘
│                       │                         │         │
│  Step 4: Calculate Statistics                   │         │
│  ┌────────────────────────────────────────────┐│         │
│  │ • Total amount                              ││         │
│  │ • Category breakdown                        ││         │
│  │ • Valid/invalid counts                      ││         │
│  └────────────────────────────────────────────┘│         │
│                       │                         │         │
│  Step 5: Build Response                        │         │
│  ┌────────────────────────────────────────────┐│         │
│  │ {                                           ││         │
│  │   is_valid: bool,                           ││         │
│  │   total_rows: int,                          ││         │
│  │   valid_rows: int,                          ││         │
│  │   invalid_rows: int,                        ││         │
│  │   total_amount: float,                      ││         │
│  │   category_breakdown: {...},                ││         │
│  │   transactions: [...],  ◄───────────────────┘│         │
│  │   errors: [...]  ◄──────────────────────────┘         │
│  │ }                                                      │
│  └────────────────────────────────────────────┘          │
│                       │                                   │
└───────────────────────┼───────────────────────────────────┘
                        │
                        │ 2. JSON Response
                        ▼
                 ┌─────────────┐
                 │   Client    │
                 │  (Browser)  │
                 └─────────────┘
```

---

## Data Flow: Save to Database (Optional)

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       │ 1. POST /api/db/transactions
       │    [Transaction, Transaction, ...]
       ▼
┌──────────────────────────────────────────────────────┐
│        FastAPI: save_transactions_to_db()            │
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │ For each Transaction:                       │    │
│  │   1. Create TransactionDB object            │    │
│  │   2. Add to database session                │    │
│  └────────────────────────────────────────────┘    │
│                      │                              │
│                      ▼                              │
│         ┌────────────────────────┐                 │
│         │   database.py          │                 │
│         │   SQLAlchemy Session   │                 │
│         └────────────┬───────────┘                 │
│                      │                              │
│                      │ db.add()                     │
│                      │ db.commit()                  │
│                      ▼                              │
└──────────────────────┼──────────────────────────────┘
                       │
                       │ SQL INSERT
                       ▼
            ┌──────────────────────┐
            │  PostgreSQL Database │
            │  transactions table  │
            └──────────────────────┘
```

---

## Component Responsibilities

### `main.py` - Application Entry Point
**Responsibilities:**
- FastAPI app initialization
- Route definitions
- Request/response handling
- Business logic orchestration
- Error handling

**Key Functions:**
- `upload_csv()` - CSV validation and parsing
- `save_transactions_to_db()` - Persist to database
- `get_transactions_from_db()` - Query database
- `get_transaction_stats()` - Aggregated statistics

---

### `models.py` - Data Models & Validation
**Responsibilities:**
- Define data structures
- Input validation
- Type conversion
- Business rule enforcement

**Key Classes:**
- `Transaction` - Validated transaction model
  - Date format validation
  - Category normalization
  - Amount validation (positive, rounded)
- `Expense` - Simple expense model
- `ExpenseUpdate` - Partial update model

---

### `database.py` - Database Layer
**Responsibilities:**
- Database connection management
- ORM model definitions
- Session handling
- Schema initialization

**Key Components:**
- `TransactionDB` - SQLAlchemy model
- `get_db()` - Session dependency
- `init_db()` - Schema creation
- `DATABASE_URL` - Connection string

---

### `static/js/app.js` - Frontend Logic
**Responsibilities:**
- User interaction handling
- File upload with progress
- API communication
- Dynamic UI updates

**Key Features:**
- Drag & drop file upload
- XHR progress tracking
- Form submission
- Table rendering

---

## Validation Pipeline

```
CSV File
   │
   ▼
┌─────────────────────────────────────┐
│ Level 1: File Validation            │
│ • Extension check (.csv)             │
│ • Size limit (5 MB)                  │
│ • Encoding (UTF-8)                   │
└────────────┬────────────────────────┘
             │ Pass
             ▼
┌─────────────────────────────────────┐
│ Level 2: Structure Validation       │
│ • Required columns present           │
│ • Header row exists                  │
│ • Not empty                          │
└────────────┬────────────────────────┘
             │ Pass
             ▼
┌─────────────────────────────────────┐
│ Level 3: Data Type Validation       │
│ • Amount is numeric                  │
│ • Date is string                     │
│ • All fields present                 │
└────────────┬────────────────────────┘
             │ Pass
             ▼
┌─────────────────────────────────────┐
│ Level 4: Business Rule Validation   │
│ • Date format (YYYY-MM-DD)           │
│ • Date is valid calendar date        │
│ • Category not empty                 │
│ • Description not empty              │
│ • Amount > 0                         │
│ • Amount rounded to 2 decimals       │
└────────────┬────────────────────────┘
             │ Pass
             ▼
      Valid Transaction
```

---

## Error Handling Strategy

### HTTP Status Codes
- `200 OK` - Successful validation (may contain invalid rows)
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid file format or missing columns
- `404 Not Found` - Resource not found
- `413 Payload Too Large` - File exceeds 5 MB
- `500 Internal Server Error` - Database or server error

### Error Response Format
```json
{
  "detail": "Missing required columns: date, amount"
}
```

### Validation Error Format
```json
{
  "is_valid": false,
  "errors": [
    {
      "row": 3,
      "data": {...},
      "errors": "date: Invalid date format"
    }
  ]
}
```

---

## Database Schema

```sql
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    date VARCHAR NOT NULL,
    category VARCHAR NOT NULL,
    description VARCHAR NOT NULL,
    amount FLOAT NOT NULL,
    created_at VARCHAR DEFAULT NOW()
);

CREATE INDEX idx_date ON transactions(date);
CREATE INDEX idx_category ON transactions(category);
```

---

## Security Considerations

✅ **Implemented:**
- File size limits (5 MB)
- File type validation (.csv only)
- Encoding validation (UTF-8)
- SQL injection prevention (ORM)
- Input validation (Pydantic)

⚠️ **Future Enhancements:**
- Rate limiting
- Authentication/Authorization
- CSRF protection
- File content scanning
- User quotas

---

## Performance Optimizations

✅ **Current:**
- Connection pooling (SQLAlchemy)
- Indexed database columns
- Batch inserts
- Streaming file upload

🔄 **Future:**
- Caching (Redis)
- Async database operations
- Background job processing
- CDN for static files

---

## Deployment Architecture

```
┌──────────────────────────────────────────────────┐
│                 Production Setup                  │
│                                                   │
│  ┌────────────┐      ┌──────────────┐           │
│  │   Nginx    │─────▶│   Uvicorn    │           │
│  │  (Reverse  │      │   (FastAPI)  │           │
│  │   Proxy)   │      │              │           │
│  └────────────┘      └──────┬───────┘           │
│                              │                    │
│                              ▼                    │
│                     ┌─────────────────┐          │
│                     │   PostgreSQL    │          │
│                     │    Database     │          │
│                     └─────────────────┘          │
└──────────────────────────────────────────────────┘
```

**Recommended Stack:**
- **Web Server:** Nginx (reverse proxy, static files)
- **App Server:** Uvicorn with multiple workers
- **Database:** PostgreSQL with connection pooling
- **Monitoring:** Prometheus + Grafana
- **Logging:** ELK Stack or CloudWatch

---

This architecture provides a solid foundation for a production-ready expense tracking application with comprehensive validation, optional persistence, and room for future enhancements.
