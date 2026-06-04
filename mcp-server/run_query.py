"""
Run a real dbo.SearchFAQ query against Azure SQL and print JSON results.

Usage:
    python run_query.py "how do i track my order?"

This script reads `AZURE_SQL_CONN_STR` from the environment (or .env files),
connects via `pyodbc`, executes `EXEC dbo.SearchFAQ @user_question = ?`, and
prints the JSON array of results. Errors are printed as JSON with an `error`
field.
"""

import os
import sys
import json
from pathlib import Path

try:
    import pyodbc
except Exception as e:
    print(json.dumps({"error": f"pyodbc import failed: {e}"}))
    raise


def load_dotenvs():
    try:
        from dotenv import load_dotenv
    except Exception:
        return
    here = Path(__file__).parent
    for p in [here / ".env", here.parent / ".env", here.parent / "AgentRAG" / ".env"]:
        if p.exists():
            load_dotenv(p, override=False)


def main():
    load_dotenvs()
    question = sys.argv[1] if len(sys.argv) > 1 else "how do i track my order?"
    conn_str = os.environ.get("AZURE_SQL_CONN_STR")

    if not conn_str:
        print(json.dumps({"error": "AZURE_SQL_CONN_STR is not set in environment"}))
        return

    try:
        conn = pyodbc.connect(conn_str, timeout=30)
        try:
            cur = conn.cursor()
            cur.execute("EXEC dbo.SearchFAQ @user_question = ?", question)
            cols = [c[0] for c in cur.description] if cur.description else []
            rows = [dict(zip(cols, row)) for row in cur.fetchall()]
            print(json.dumps(rows, default=str))
        finally:
            conn.close()
    except Exception as e:
        print(json.dumps({"error": str(e)}))


if __name__ == "__main__":
    main()
