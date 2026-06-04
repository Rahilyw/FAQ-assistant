"""
FAQ Assistant – MCP Server

Exposes a single `search_faq` tool that queries Azure SQL via the
dbo.SearchFAQ stored procedure and returns results to any MCP client
(e.g. Microsoft Foundry agent portal).

Start:  python server.py
Stop:   Ctrl+C
"""

import os
import json
import pyodbc
from pathlib import Path
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Load environment variables – cascade: local .env → root .env → AgentRAG/.env
# ---------------------------------------------------------------------------
_here = Path(__file__).parent
for _env in [
    _here / ".env",
    _here.parent / ".env",
    _here.parent / "AgentRAG" / ".env",
]:
    if _env.exists():
        load_dotenv(_env, override=False)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SQL_CONN_STR = os.environ["AZURE_SQL_CONN_STR"]   # fail fast if missing
MCP_HOST     = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT     = int(os.getenv("MCP_PORT", "8000"))

# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------
mcp = FastMCP(
    "FAQ SQL Assistant",
    host=MCP_HOST,
    port=MCP_PORT,
    stateless_http=True,   # no session state needed for a simple RAG tool
)

def _query_faq(user_question: str) -> list[dict]:
    """Execute dbo.SearchFAQ and return rows as a list of dicts."""
    conn = pyodbc.connect(SQL_CONN_STR, timeout=30)
    try:
        cursor = conn.cursor()
        cursor.execute("EXEC dbo.SearchFAQ @user_question = ?", user_question)
        columns = [col[0] for col in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return rows
    finally:
        conn.close()


@mcp.tool()
def search_faq(user_question: str) -> str:
    """
    Search the FAQ knowledge base for answers related to the user's question.

    Args:
        user_question: The question or topic to look up in the FAQ database.

    Returns:
        A JSON string containing matching FAQ entries with category, question,
        and answer fields.
    """
    rows = _query_faq(user_question)
    if not rows:
        return json.dumps({"results": [], "message": "No matching FAQ entries found."})
    return json.dumps({"results": rows}, default=str)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print(f"[MCP] Starting FAQ SQL Assistant on http://{MCP_HOST}:{MCP_PORT}")
    print(f"[MCP] MCP endpoint : http://{MCP_HOST}:{MCP_PORT}/mcp")
    print(f"[MCP] For Foundry  : replace 0.0.0.0 with your dev-tunnel URL")
    print("[MCP] Press Ctrl+C to stop\n")

    try:
        import uvicorn
        uvicorn.run(
            mcp.streamable_http_app(),
            host=MCP_HOST,
            port=MCP_PORT,
            log_level="info",
        )
    except Exception:
        mcp.run(transport="streamable-http")
