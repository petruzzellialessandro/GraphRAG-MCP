# GraphRAG MCP Server

An [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) server that exposes a **Microsoft GraphRAG** knowledge graph as a set of queryable tools for AI assistants (Claude, GitHub Copilot, etc.).

It combines GraphRAG-native retrieval strategies:
- **Basic search** — baseline GraphRAG retrieval for straightforward RAG-style questions
- **Local search** — entity-focused, context-grounded answers using the knowledge graph
- **Global search** — thematic map-reduce search across community reports

---

## Architecture

```
MCP Client (Claude / Copilot / etc.)
        │  SSE over HTTP
        ▼
run_mcp_server.py ──► uvicorn ──► mcp_server/server.py  (FastMCP 0.2)
                                        │
                    ┌───────────────────┼─────────────────────┐
                    ▼                   ▼                     ▼
          basic_search          local_search          global_search
                                                     list_entities
                                                     get_entity
                    │                   │                     │
                    ▼                   ▼                     ▼
           GraphRAG LocalSearch  GraphRAG LocalSearch  GraphRAG GlobalSearch
           (baseline path)       (entity-focused)      (map-reduce)
           core/data_loader      core/data_loader      core/data_loader
           core/source_resolver  core/source_resolver
                    │
                    ▼
            output/create_final_*.parquet  (GraphRAG artefacts)
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
│       └── entity_query.py    # list_entities + get_entity tools
├── core/
│   ├── config.py              # Pydantic-settings configuration (reads .env)
│   ├── data_loader.py         # Reads GraphRAG parquet artefacts into DataFrames
│   ├── search.py              # Unified GraphRAG v2/v3 search engine builder
│   ├── llm_factory.py         # OpenAI LLM + embedder factory
│   ├── source_resolver.py     # Maps GraphRAG context sources → document titles
│   └── version.py             # GraphRAG version detection utility
├── output/                    # GraphRAG pipeline output (parquets + LanceDB)
│   ├── create_final_entities.parquet
│   ├── create_final_relationships.parquet
│   ├── create_final_communities.parquet
│   ├── create_final_community_reports.parquet
│   ├── create_final_text_units.parquet
│   ├── create_final_documents.parquet
│   └── lancedb/               # GraphRAG's internal vector store
├── env.example                # Environment variable template
├── requirements.txt
└── pyproject.toml
```

---

## MCP Tools

| Tool | Parameters | Description |
|---|---|---|
| `basic_search` | `query: str`, `response_type: str = "Multiple Paragraphs"` | Baseline GraphRAG retrieval path for standard RAG-style questions |
| `local_search` | `query: str`, `community_level: int = 2`, `response_type: str = "Multiple Paragraphs"` | Entity-focused search — retrieves relevant entities, relationships, and text chunks to answer the query |
| `global_search` | `query: str` | Thematic search — map-reduce over all community reports to answer broad, analytical questions |
| `list_entities` | `entity_type: str \| None = None` | List up to 100 graph entities, optionally filtered by type |
| `get_entity` | `name: str` | Get full details + up to 20 direct relationships for a named entity |

---

## Prerequisites

- Python ≥ 3.10
- An OpenAI API key
- A completed **GraphRAG index** — the `output/create_final_*.parquet` files must exist

---

## Setup

### 1. Install Python dependencies

```bash
# With pip
pip install -r requirements.txt

# Or with uv
uv pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp env.example .env
```

Edit `.env` and fill in all required values:

```env
# Required
OPENAI_API_KEY=sk-...

# GraphRAG output directory (where parquet files live)
GRAPHRAG_OUTPUT_DIR=./output

# MCP server bind
MCP_HOST=127.0.0.1
MCP_PORT=8011
```

### 3. Start the MCP server

```bash
python run_mcp_server.py
```

The server starts at `http://127.0.0.1:8011`.

Available SSE endpoints:

- `/sse` -> all searches enabled (`basic_search`, `local_search`, `global_search`)
- `/basic/sse` -> only `basic_search`
- `/local/sse` -> only `local_search`
- `/global/sse` -> only `global_search`

---

## Connecting an MCP Client

### VS Code / GitHub Copilot

Add to `.vscode/mcp.json` in your workspace. Choose the URL based on the search mode you want to enable:

```json
{
  "servers": {
    "graphrag-basic": {
      "type": "sse",
      "url": "http://127.0.0.1:8011/basic/sse"
    },
    "graphrag-local": {
      "type": "sse",
      "url": "http://127.0.0.1:8011/local/sse"
    },
    "graphrag-global": {
      "type": "sse",
      "url": "http://127.0.0.1:8011/global/sse"
    },
    "graphrag-all": {
      "type": "sse",
      "url": "http://127.0.0.1:8011/sse"
    }
  }
}
```

Keep only the server entries you actually want to expose to the MCP client.

---

## Known Issues

The following outstanding gaps remain. All critical and high-severity bugs have been fixed.

---

### 1. `core/llm_factory.py` — GraphRAG API compatibility (Medium)

The `get_llm()` and `get_text_embedder()` factory functions contain separate code paths for GraphRAG v2 and v3. The exact constructor signatures for your installed version may need adjustment depending on the `graphrag` package version. Run `python -c "from core.llm_factory import get_llm; get_llm()"` to verify before starting the server.

---

### 2. `core/source_resolver.py` — Source tracing depends on GraphRAG context format (Low)

`resolve_sources()` attempts to match sources returned by the GraphRAG search engine against the `text_units` parquet. If GraphRAG's internal context dict does not include a `sources` key or uses an unexpected column name, `local_search` responses will have empty `sources`. This is handled gracefully (returns `[]`) and does not break the search answer.

---

## Dependencies

| Package | Purpose |
|---|---|
| `graphrag>=2.0` | GraphRAG index pipeline + LocalSearch/GlobalSearch engines |
| `fastmcp==0.2.0` | MCP server framework |
| `starlette>=0.37,<0.38` | ASGI framework (used by FastMCP's SSE app) |
| `uvicorn>=0.29` | ASGI server |
| `openai>=1.0` | OpenAI LLM + embeddings |
| `pandas>=2.0` + `pyarrow>=15.0` | Parquet file reading |
| `pydantic-settings>=2.0` | Settings from environment / `.env` |
| `python-dotenv>=1.0` | `.env` file loading |


---

## Generating a GraphRAG Index

If you don't yet have the `output/create_final_*.parquet` files:

```bash
pip install graphrag
graphrag init --root .
# Edit .graphrag/settings.yaml to configure your LLM and input data
graphrag index --root .
```

See the [GraphRAG documentation](https://microsoft.github.io/graphrag/) for full details.

---

## Security Notes

- `mcp_server/server.py` sets `allow_origins=["*"]` — suitable for local development only. Restrict allowed origins before any public deployment.
- The `.env` file contains secrets (e.g. `OPENAI_API_KEY`). Ensure it is listed in `.gitignore` and never committed.
