# AI-Powered FAQ Assistant

![Azure SQL](https://img.shields.io/badge/Azure%20SQL-Hyperscale-0078D4?style=flat&logo=microsoftazure&logoColor=white)
![Azure OpenAI](https://img.shields.io/badge/Azure%20OpenAI-GPT--4o-412991?style=flat&logo=openai&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)
![Microsoft Fabric](https://img.shields.io/badge/Microsoft%20Fabric-OneLake-F2C811?style=flat&logo=powerbi&logoColor=black)
![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-00B4D8?style=flat)
![License](https://img.shields.io/badge/license-MIT-green?style=flat)

An end-to-end AI-powered FAQ assistant that uses **vector semantic search** in Azure SQL Hyperscale, **Retrieval-Augmented Generation (RAG)** with GPT-4o, and **Model Context Protocol (MCP)** to ground AI responses in approved support content — with no hallucinations.

Built as part of the Microsoft Build 2026 Digital Lab

---

## Architecture

```
User Question
      ↓
Azure SQL Hyperscale  ←─── 1536-dim embeddings (Azure OpenAI)
  VECTOR_DISTANCE()
      ↓
Top 3 FAQ matches (semantic similarity)
      ↓
Grounded Prompt Assembly (T-SQL + STRING_AGG)
      ↓
GPT-4o via sp_invoke_external_rest_endpoint
      ↓
Grounded AI Answer (no hallucinations)
```

**Agent flow (Exercise 4):**
```
User → Foundry Agent → MCP tool call → Local Python server → Azure SQL → Grounded response
```

**Analytics flow (Exercise 5):**
```
Azure SQL → Fabric Mirroring (no ETL) → OneLake → SQL Analytics Endpoint → Power BI
```

---

## Key Features

- **Vector semantic search** — FAQ questions stored as 1536-dimension embeddings; cosine similarity via `VECTOR_DISTANCE` in Azure SQL
- **RAG pipeline in pure T-SQL** — retrieval, prompt assembly, and GPT-4o call all orchestrated inside Azure SQL using `sp_invoke_external_rest_endpoint`
- **Custom MCP server** — Python FastMCP server exposes a `search_faq` tool to any MCP-compatible client (Foundry Agents, VS Code Copilot)
- **Foundry Agent orchestration** — Microsoft Foundry Agent calls the MCP tool over dev tunnel; grounds every response in retrieved FAQ content
- **Data API Builder (DAB)** — Microsoft-native MCP layer exposing Azure SQL as a read-only tool without writing custom API code
- **Fabric Mirroring** — `FAQ_Content` auto-synced into OneLake in near real-time; Power BI report built directly on mirrored data
- **Hallucination prevention** — agent and SQL pipeline both instructed to respond "I do not know" when no relevant FAQ content is found

---

## Project Structure

```
├── sql-scripts/
│   └── rag_pipeline.sql        # Full RAG pipeline: vector retrieval + GPT-4o call
├── mcp-server/
│   ├── server.py               # FastMCP server exposing search_faq tool
│   ├── invoke_mcp.py           # CLI test client for the MCP server
│   ├── run_query.py            # Direct SQL query runner (no MCP)
│   ├── diag_pyodbc.py          # Connection string diagnostic utility
│   ├── requirements.txt
│   └── .env.example            # Environment variable template
├── dab-config/
│   └── dab-config.json         # Data API Builder MCP configuration
└── README.md
```

---

## Setup

### Prerequisites

- Python 3.10+
- [ODBC Driver 17 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
- Azure SQL Database with `dbo.FAQ_Content`, `dbo.FAQ_Embeddings`, and `dbo.SearchFAQ` stored procedure
- Azure OpenAI deployment (GPT-4o)

### MCP Server

1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   .venv\Scripts\Activate.ps1        # Windows
   source .venv/bin/activate          # macOS/Linux
   pip install -r mcp-server/requirements.txt
   ```

2. Copy `.env.example` to `.env` and fill in your connection string:
   ```
   AZURE_SQL_CONN_STR=Driver={ODBC Driver 17 for SQL Server};Server=<server>.database.windows.net;Database=<db>;Uid=<user>;Pwd=<password>;Encrypt=yes
   ```

3. Start the server:
   ```bash
   python mcp-server/server.py
   ```
   Server runs at `http://0.0.0.0:8000/mcp`

4. Test it:
   ```bash
   python mcp-server/invoke_mcp.py "how do I track my order?"
   ```

### RAG Pipeline (SQL)

Open `sql-scripts/rag_pipeline.sql` in VS Code with the MSSQL extension. Replace the placeholder API key and endpoint URL with your Azure OpenAI values, then run the script.

### Data API Builder (DAB)

1. Install DAB (.NET SDK required):
   ```bash
   dotnet new tool-manifest
   dotnet tool install microsoft.dataapibuilder
   ```

2. Update the connection string placeholder in `dab-config/dab-config.json`.

3. Start the MCP server:
   ```bash
   dotnet tool run dab start --mcp-stdio role:anonymous --config dab-config/dab-config.json
   ```

---

## Tech Stack

| Component | Role |
|---|---|
| Azure SQL Hyperscale | Vector storage, RAG retrieval, REST API calls |
| Azure OpenAI (GPT-4o) | Embedding generation + answer generation |
| Python FastMCP | Custom MCP server (search_faq tool) |
| Microsoft Foundry Agents | Agent orchestration layer |
| Data API Builder | Microsoft-native MCP layer for Azure SQL |
| Microsoft Fabric + OneLake | Near real-time analytics mirroring |
| Power BI | FAQ analytics and reporting |
| dev tunnel | Expose local MCP server to cloud Foundry |

---

## What I Learned

- How **vector embeddings** enable semantic search that goes beyond keyword matching
- How to implement a complete **RAG pipeline entirely in T-SQL** — no Python required for retrieval
- How **Model Context Protocol (MCP)** standardizes tool interfaces for AI agents
- How **Microsoft Fabric Mirroring** eliminates ETL pipelines for analytics on operational data
- The difference between a grounded AI response and a hallucinated one — and how to enforce grounding

---

*Built at Microsoft Build 2026 — LAB513D*
