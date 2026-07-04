# Expense Tracker — Web App

A full-stack expense tracking application with a **FastAPI** backend and a vanilla HTML/CSS/JS frontend.

---

## Project Structure

```
web/
├── main.py              # FastAPI application & API routes
├── requirements.txt     # Python dependencies
├── templates/
│   └── index.html       # Landing page (served by FastAPI)
└── static/
    ├── css/
    │   └── style.css    # Dark-theme stylesheet
    └── js/
        └── app.js       # Frontend logic (upload, forms, fetch calls)
```

---

## Prerequisites

- **Python 3.10+** — [python.org/downloads](https://www.python.org/downloads/)
- **pip** (bundled with Python)

Verify your installation:

```bash
python --version
pip --version
```

---

## Installation

1. **Clone the repository** (or navigate to the project folder):

   ```bash
   cd /path/to/expense-tracker/web
   ```

2. **Create and activate a virtual environment** (recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate        # macOS / Linux
   .venv\Scripts\activate           # Windows
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

---

## Running the App

Start the development server from inside the `web/` folder:

```bash
uvicorn main:app --reload
```

| Option | Description |
|--------|-------------|
| `main` | The Python module (`main.py`) |
| `app`  | The FastAPI instance inside that module |
| `--reload` | Auto-restarts the server when you save a file |

The server starts at **http://localhost:8000** by default.

---

## Accessing the App

| URL | Description |
|-----|-------------|
| `http://localhost:8000` | Landing page |
| `http://localhost:8000/docs` | Interactive API docs (Swagger UI) |
| `http://localhost:8000/redoc` | Alternative API docs (ReDoc) |

---

## API Endpoints

### Pages

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Serves the HTML landing page |

### Expenses

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/expenses` | Returns all expenses |
| `GET` | `/api/expenses/{id}` | Returns a single expense by ID |
| `POST` | `/api/expenses` | Creates a new expense |
| `PUT` | `/api/expenses/{id}` | Partially updates an existing expense |

**POST / PUT request body** (`application/json`):

```json
{
  "description": "Groceries",
  "amount": 54.32,
  "category": "Food"
}
```

### CSV Upload

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/upload-csv` | Upload a `.csv` file; returns parsed rows as JSON |

**Rules:**
- File must have a `.csv` extension and be UTF-8 encoded.
- Maximum file size: **5 MB**.
- The first row is treated as the header row.

**Example response:**

```json
{
  "filename": "transactions.csv",
  "rows": 120,
  "columns": ["date", "description", "amount", "category"],
  "data": [
    { "date": "2026-01-01", "description": "Coffee", "amount": "4.50", "category": "Food" }
  ]
}
```

---

## Stopping the Server

Press `Ctrl + C` in the terminal where `uvicorn` is running.

---

## Notes

- Expense data is stored **in memory** and will be lost when the server restarts. To persist data, replace the `expenses` dict in `main.py` with a database (e.g., SQLite via SQLAlchemy).
- The frontend is intentionally dependency-free — no build step or bundler required.
