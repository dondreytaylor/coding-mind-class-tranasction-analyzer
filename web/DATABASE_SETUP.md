# Postgres Database Setup Guide

This guide explains how to set up and use PostgreSQL with the Expense Tracker web application.

## Prerequisites

- **PostgreSQL** installed locally
- **Python 3.10+**
- **pip** package manager

---

## Step 1: Install PostgreSQL

### macOS (using Homebrew)
```bash
brew install postgresql@15
brew services start postgresql@15
```

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### Windows
Download and install from [postgresql.org/download/windows](https://www.postgresql.org/download/windows/)

---

## Step 2: Create Database and User

1. **Access PostgreSQL shell:**
   ```bash
   psql postgres
   ```

2. **Create a database:**
   ```sql
   CREATE DATABASE expense_tracker;
   ```

3. **Create a user (optional but recommended):**
   ```sql
   CREATE USER expense_user WITH PASSWORD 'your_secure_password';
   GRANT ALL PRIVILEGES ON DATABASE expense_tracker TO expense_user;
   ```

4. **Exit the shell:**
   ```sql
   \q
   ```

---

## Step 3: Install Python Dependencies

From the `web/` directory:

```bash
pip install -r requirements.txt
```

This installs:
- `sqlalchemy>=2.0.0` - ORM for database operations
- `psycopg2-binary>=2.9.0` - PostgreSQL adapter for Python

---

## Step 4: Configure Database Connection

Set the `DATABASE_URL` environment variable before starting the server:

### Default (no authentication)
```bash
export DATABASE_URL="postgresql://localhost:5432/expense_tracker"
```

### With username and password
```bash
export DATABASE_URL="postgresql://expense_user:your_secure_password@localhost:5432/expense_tracker"
```

### For Windows (PowerShell)
```powershell
$env:DATABASE_URL="postgresql://localhost:5432/expense_tracker"
```

---

## Step 5: Start the Application

The database tables will be created automatically on startup:

```bash
uvicorn main:app --reload
```

You should see:
```
Database initialized successfully!
Database tables created successfully!
```

---

## API Endpoints for Database Operations

Once the database is set up, you can use these endpoints:

### 1. Save Transactions to Database
**POST** `/api/db/transactions`

```bash
curl -X POST "http://localhost:8000/api/db/transactions" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "date": "2026-07-01",
      "category": "food",
      "description": "Lunch",
      "amount": 15.50
    }
  ]'
```

### 2. Get All Transactions from Database
**GET** `/api/db/transactions`

```bash
curl "http://localhost:8000/api/db/transactions"
```

Optional query parameters:
- `category` - Filter by category (e.g., `?category=food`)
- `limit` - Limit results (default: 100)

### 3. Get Transaction Statistics
**GET** `/api/db/stats`

```bash
curl "http://localhost:8000/api/db/stats"
```

Returns aggregated statistics including total amount and category breakdown.

---

## Complete Workflow Example

### 1. Upload and validate a CSV file
```bash
curl -X POST "http://localhost:8000/api/upload-csv" \
  -F "file=@transactions.csv"
```

### 2. Save validated transactions to database
Take the `transactions` array from the upload response and POST it:

```bash
curl -X POST "http://localhost:8000/api/db/transactions" \
  -H "Content-Type: application/json" \
  -d '<transactions_array_from_upload_response>'
```

### 3. Query your data
```bash
# Get all transactions
curl "http://localhost:8000/api/db/transactions"

# Get only food transactions
curl "http://localhost:8000/api/db/transactions?category=food"

# Get statistics
curl "http://localhost:8000/api/db/stats"
```

---

## Database Schema

The `transactions` table has the following structure:

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key (auto-increment) |
| `date` | VARCHAR | Transaction date (YYYY-MM-DD) |
| `category` | VARCHAR | Transaction category (indexed) |
| `description` | VARCHAR | Transaction description |
| `amount` | FLOAT | Transaction amount |
| `created_at` | VARCHAR | Timestamp when record was created |

---

## Troubleshooting

### Connection Error
If you see "could not connect to server":
```bash
# Check if PostgreSQL is running
brew services list  # macOS
sudo systemctl status postgresql  # Linux
```

### Authentication Failed
Verify your credentials in the `DATABASE_URL`:
```bash
psql -U expense_user -d expense_tracker -h localhost
```

### Module Not Found
Ensure dependencies are installed:
```bash
pip install sqlalchemy psycopg2-binary
```

---

## Testing the Database

You can verify the database directly using `psql`:

```bash
psql -d expense_tracker

# List all tables
\dt

# View transactions
SELECT * FROM transactions;

# Count transactions by category
SELECT category, COUNT(*), SUM(amount) 
FROM transactions 
GROUP BY category;
```

---

## Notes

- The application works **without** PostgreSQL - database features are optional
- If PostgreSQL is not configured, the app will print a warning and continue with in-memory storage
- All database operations are wrapped in try-catch blocks for graceful error handling
- The database connection uses connection pooling via SQLAlchemy for efficiency
