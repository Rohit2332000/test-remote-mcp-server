from fastmcp import FastMCP
import os
import aiosqlite
import sqlite3
import tempfile
import json

# -----------------------------
# Cloud-safe paths
# -----------------------------
TEMP_DIR = tempfile.gettempdir()
DB_PATH = os.path.join(TEMP_DIR, "expenses.db")

# -----------------------------
# Default categories (no files)
# -----------------------------
DEFAULT_CATEGORIES = {
    "categories": [
        "Food & Dining",
        "Transportation",
        "Shopping",
        "Entertainment",
        "Bills & Utilities",
        "Healthcare",
        "Travel",
        "Education",
        "Business",
        "Other"
    ]
}

# -----------------------------
# MCP Server
# -----------------------------
mcp = FastMCP("ExpenseTracker")


# -----------------------------
# Initialize SQLite DB (sync)
# Runs only when server starts, not at import-time.
# -----------------------------
def init_db():
    try:
        with sqlite3.connect(DB_PATH) as c:
            # WAL not allowed on Cloud → skip
            c.execute("""
                CREATE TABLE IF NOT EXISTS expenses(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    subcategory TEXT DEFAULT '',
                    note TEXT DEFAULT ''
                )
            """)
            print("Database initialized at:", DB_PATH)

    except Exception as e:
        print("Database initialization error:", e)
        raise


# -----------------------------
# MCP Tools
# -----------------------------
@mcp.tool()
async def add_expense(date, amount, category, subcategory="", note=""):
    """Add a new expense entry to the database."""
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            cur = await c.execute(
                "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
                (date, amount, category, subcategory, note)
            )
            await c.commit()
            return {
                "status": "success",
                "id": cur.lastrowid,
                "message": "Expense added successfully"
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
async def list_expenses(start_date, end_date):
    """List expense entries in date range."""
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            cur = await c.execute(
                """
                SELECT id, date, amount, category, subcategory, note
                FROM expenses
                WHERE date BETWEEN ? AND ?
                ORDER BY date DESC, id DESC
                """,
                (start_date, end_date)
            )
            rows = await cur.fetchall()
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in rows]

    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
async def summarize(start_date, end_date, category=None):
    """Summarize expenses by category."""
    try:
        query = """
            SELECT category, SUM(amount) AS total_amount, COUNT(*) as count
            FROM expenses
            WHERE date BETWEEN ? AND ?
        """
        params = [start_date, end_date]

        if category:
            query += " AND category = ?"
            params.append(category)

        query += " GROUP BY category ORDER BY total_amount DESC"

        async with aiosqlite.connect(DB_PATH) as c:
            cur = await c.execute(query, params)
            rows = await cur.fetchall()
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in rows]

    except Exception as e:
        return {"status": "error", "message": str(e)}


# -----------------------------
# MCP Resource
# -----------------------------
@mcp.resource("expense:///categories", mime_type="application/json")
def categories():
    """Return the list of default categories as JSON."""
    return json.dumps(DEFAULT_CATEGORIES, indent=2)


# -----------------------------
# Start MCP Server
# -----------------------------
if __name__ == "__main__":
    init_db()  # Only run on server startup
    mcp.run(transport="http", host="0.0.0.0", port=8000)
