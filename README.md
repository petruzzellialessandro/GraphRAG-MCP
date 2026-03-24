# GraphRAG MCP Server

An [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) server that exposes a **Microsoft GraphRAG** knowledge graph as a set of queryable tools for AI assistants (Claude, GitHub Copilot, etc.).

It combines GraphRAG-native retrieval strategies:
- **Basic search** — baseline GraphRAG retrieval for straightforward RAG-style questions
- **Local search** — entity-focused, context-grounded answers using the knowledge graph
- **Global search** — thematic map-reduce search across community reports
- **Drift search** — Entity + Community hybrid search combining local and global insights

---

## Architecture

```
MCP Client (Claude / Copilot / etc.)
        │  SSE over HTTP
        ▼
run_mcp_server.py ──► uvicorn ──► mcp_server/server.py  (FastMCP 0.2)
                                        │
                    ┌───────────┬───────┼────────┬────────────┐
                    ▼           ▼       ▼        ▼            ▼
          basic_search  local_search  global_search  drift_search
                                      list_entities
                                      get_entity
                    │           │       │        │            │
                    ▼           ▼       ▼        ▼            ▼
           GraphRAG LocalSearch  GraphRAG LocalSearch  GraphRAG DriftSearch
                                      GraphRAG GlobalSearch
                    └───────────┴───────┬────────┴────────────┘
                                        │
                                        ▼
           core/data_loader      core/data_loader      core/data_loader
           core/source_resolver  core/source_resolver
                    │
                    ▼
            output/create_final_*.parquet  (GraphRAG artifacts)
```

### Directory Layout

```
.
├── run_mcp_server.py          # Entry point — starts uvicorn
├── mcp_server/
│   ├── server.py              # FastMCP app, tool registrations, CORS middleware
│   └── tools/
│       ├── basic_search.py    # basic_search tool implementation
│       ├── local_search.py    # local_search tool implementation
│       ├── global_search.py   # global_search tool implementation
│       ├── drift_search.py    # drift_search tool implementation
│       └── entity_query.py    # list_entities + get_entity tools
├── core/
│   ├── config.py              # Pydantic-settings configuration (reads .env)
│   ├── data_loader.py         # Reads GraphRAG parquet artifacts into DataFrames
│   ├── search.py              # Unified GraphRAG v2/v3 search engine builder
│   ├── llm_factory.py         # OpenAI LLM + embedder factory
│   ├── source_resolver.py     # Maps GraphRAG context sources → document titles
│   └── version.py             # GraphRAG version detection utility
├── env.example                # Environment variable template
├── requirements.txt
└── pyproject.toml
```

---

## MCP Tools

| Tool | Parameters | Description |
|---|---|---|
| `basic_search` | `query: str`, `response_type: str = "Multiple Paragraphs"` | Baseline GraphRAG retrieval for standard RAG-style questions |
| `local_search` | `query: str`, `community_level: int = 2`, `response_type: str = "Multiple Paragraphs"` | Entity-focused search — retrieves relevant entities, relationships, and text chunks |
| `global_search` | `query: str` | Thematic search — map-reduce over all community reports to answer broad, analytical questions |
| `drift_search` | `query: str`, `community_level: int = 2`, `response_type: str = "Multiple Paragraphs"` | Entity + Community hybrid search combining local and global insights |
| `list_entities` | `entity_type: str \| None = None` | List up to 100 graph entities, optionally filtered by type |
| `get_entity` | `name: str` | Get full details + up to 20 direct relationships for a named entity |

---

## Complete Setup Guide

Follow these steps to get the entire pipeline running, from zero to a working MCP server.

### 1. Install Dependencies

Ensure you have Python 3.10 or higher.

```bash
# With pip
pip install -r requirements.txt

# Or with uv (recommended for speed)
uv pip install -r requirements.txt
```

### 2. Generate GraphRAG Index

The MCP server needs a pre-built GraphRAG index (`output/*.parquet`) to function.

1.  **Initialize GraphRAG:**
    ```bash
    graphrag init --root .
    ```
    This creates a `.graphrag/` directory with `settings.yaml` and `.env`.

2.  **Configure GraphRAG:**
    Edit `.graphrag/.env` (or your main `.env` if you merge them) to add your API Key:
    ```env
    GRAPHRAG_API_KEY=sk-...
    ```

3.  **Run Indexing:**
    Place your raw text documents in an `input/` folder (create it if missing), then run:
    ```bash
    mkdir -p input
    # Copy your .txt files into input/
    graphrag index --root .
    ```
    This process can take minutes to hours. When finished, artifacts will be in `output/`.

### 3. Configure the MCP Server

Create a `.env` file for the MCP server:

```bash
cp env.example .env
```

Edit the `.env` file and fill in the required values:

```env
# [Required] OpenAI API Key
OPENAI_API_KEY=sk-...

# [Required] Path to the GraphRAG output directory containing the parquet files
GRAPHRAG_OUTPUT_DIR=./output

# [Optional] Host and Port for the MCP server
MCP_HOST=127.0.0.1
MCP_PORT=8011
```

### 4. Start the MCP Server

Run the server using the provided script:

```bash
python run_mcp_server.py
```

Available SSE endpoints:
- `http://127.0.0.1:8011/sse` (All tools)
- `http://127.0.0.1:8011/basic/sse`
- `http://127.0.0.1:8011/local/sse`
- `http://127.0.0.1:8011/global/sse`
- `http://127.0.0.1:8011/drift/sse`

### 5. Connect an MCP Client

#### VS Code (Github Copilot)

Add the server configuration to your workspace's `.vscode/mcp.json` file:

```json
{
  "servers": {
    "graphrag": {
      "type": "sse",
      "url": "http://127.0.0.1:8011/sse"
    }
  }
}
```

Or for selective access:

```json
{
  "servers": {
    "graphrag-local": {
      "type": "sse",
      "url": "http://127.0.0.1:8011/local/sse"
    },
    "graphrag-drift": {
      "type": "sse",
      "url": "http://127.0.0.1:8011/drift/sse"
    }
  }
}
```

Reload VS Code to apply changes.

---

## Troubleshooting

-   **"No such file or directory: .../create_final_*.parquet"**:
    Ensure `GRAPHRAG_OUTPUT_DIR` in `.env` points to the correct folder containing the parquet files.

-   **GraphRAG version mismatch**:
    This server is designed for GraphRAG v2/v3 artifacts. Ensure your `graphrag` package version matches the one used to create the index.

---
> [!CAUTION]
> ## Known Bugs & Fixes

### 1. LiteLLM Errors

If you encounter issues with `litellm` (which GraphRAG uses internally), you may need to install the latest version from source:

```bash
pip install graphrag==2.7.1
# Clone the repository
git clone https://github.com/BerriAI/litellm.git
cd litellm

# Install development dependencies and the package in editable mode
make install-dev
pip install -e .

# Run validation checks (optional)
make format
make lint
make test-unit
```

This installs your local `litellm` clone into the current Python environment (venv), overriding the PyPI version.

### 2. OpenAI "max_tokens" Error

If you see the error:
`Invalid type for 'max_tokens': expected an unsupported value, but got null instead.`

This is a known issue (microsoft/graphrag#1976). To fix it, you need to patch the `openai` package in your virtual environment.

1.  Locate `openai/resources/chat/completions/completions.py` inside your site-packages:
    -   **Windows:** `venv\Lib\site-packages\openai\resources\chat\completions\completions.py`
    -   **Linux/Mac:** `.venv/lib/python3.x/site-packages/openai/resources/chat/completions/completions.py`

2.  Open the file and remove **all** occurrences of `"max_tokens": max_tokens,`.

---

## Security Notes

-   **CORS**: `mcp_server/server.py` sets `allow_origins=["*"]`, suitable for local development only.
-   **Secrets**: Ensure `.env` is listed in your `.gitignore` and never committed.
