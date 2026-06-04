# AI-Powered FAQ Assistant

An end-to-end AI FAQ assistant built on Azure SQL Hyperscale, Azure OpenAI, Microsoft Fabric, and Microsoft Foundry Agents.

## Architecture

```
User Question
      ↓
Azure SQL Hyperscale (Vector Search)
      ↓
Top 3 FAQ matches (semantic similarity)
      ↓
Grounded Prompt Assembly (T-SQL)
      ↓
GPT-4o via Azure OpenAI (sp_invoke_external_rest_endpoint)
      ↓
Grounded AI Answer
```

## Key Features

- **Vector semantic search** – FAQ questions stored as 1536-dimension embeddings; similarity search via `VECTOR_DISTANCE` in Azure SQL
- **RAG pipeline in T-SQL** – entire retrieval + prompt assembly + GPT-4o call orchestrated inside Azure SQL using `sp_invoke_external_rest_endpoint`
- **MCP server** – Python FastMCP server exposes `search_faq` tool to any MCP-compatible client (Foundry Agents, VS Code Copilot)
- **Foundry Agent orchestration** – Microsoft Foundry Agent calls the MCP tool via dev tunnel to retrieve grounded FAQ answers
- **Data API Builder (DAB)** – Microsoft-native MCP layer exposing Azure SQL as a read-only MCP tool without custom API code
- **Fabric Mirroring** – `FAQ_Content` mirrored into OneLake in near real-time; queried via SQL Analytics Endpoint and visualized in Power BI

## Project Structure

```
├── sql-scripts/
│   └── rag_pipeline.sql        # Full RAG pipeline: retrieval + GPT-4o call
├── mcp-server/
│   ├── server.py               # FastMCP server exposing search_faq tool
│   ├── invoke_mcp.py           # Test client for the MCP server
│   ├── diag_pyodbc.py          # Connection string diagnostic utility
│   ├── requirements.txt
│   └── .env.example            # Environment variable template
├── dab-config/
│   └── dab-config.json         # Data API Builder MCP configuration
└── README.md
```

## Setup

### MCP Server

1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r mcp-server/requirements.txt
   ```

2. Copy `.env.example` to `.env` and fill in your Azure SQL connection string:
   ```
   AZURE_SQL_CONN_STR=Driver={ODBC Driver 17 for SQL Server};Server=<server>.database.windows.net;...
   ```

3. Start the server:
   ```bash
   python mcp-server/server.py
   ```

### RAG Pipeline (SQL)

Open `sql-scripts/rag_pipeline.sql` in VS Code with the MSSQL extension connected to your Azure SQL database. Replace the placeholder API key and endpoint URL with your Azure OpenAI values, then run the script.

### Data API Builder (DAB)

1. Install DAB:
   ```bash
   dotnet tool install microsoft.dataapibuilder
   ```

2. Update the connection string in `dab-config/dab-config.json`.

3. Start the MCP server:
   ```bash
   dotnet tool run dab start --mcp-stdio role:anonymous --config dab-config/dab-config.json
   ```

## Tech Stack

| Component | Role |
|---|---|
| Azure SQL Hyperscale | Vector storage + RAG retrieval |
| Azure OpenAI (GPT-4o) | Answer generation |
| Python FastMCP | Custom MCP server |
| Microsoft Foundry Agents | Agent orchestration |
| Data API Builder | Native MCP layer for Azure SQL |
| Microsoft Fabric | Analytics + Power BI reporting |
| dev tunnel | Expose local MCP server to Foundry |
