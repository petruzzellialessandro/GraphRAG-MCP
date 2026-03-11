from mcp.server.fastmcp import FastMCP
from starlette.middleware.cors import CORSMiddleware
from mcp_server.tools.local_search import local_search_tool
from mcp_server.tools.basic_search import basic_search_tool
from mcp_server.tools.global_search import global_search_tool
from mcp_server.tools.entity_query import list_entities_tool, get_entity_tool

# FastMCP 0.2.0: only "name" param — no "version"
mcp = FastMCP(name="graphrag-mcp-server")

@mcp.tool()
async def local_search(
    query: str,
    community_level: int = 2,
    response_type: str = "Multiple Paragraphs",
) -> dict:
    """
    Entity-focused search on the knowledge graph.
    Best for: 'Who leads project X?', 'What is the relation between A and B?'
    """
    return await local_search_tool(query, community_level=community_level,
                                    response_type=response_type)


@mcp.tool()
async def basic_search(
    query: str,
    response_type: str = "Multiple Paragraphs",
) -> dict:
    """
    Baseline GraphRAG retrieval for straightforward factual questions.
    Uses GraphRAG LocalSearch without custom hybrid/vector fusion layers.
    """
    return await basic_search_tool(query, response_type=response_type)

@mcp.tool()
async def global_search(query: str) -> dict:
    """
    Thematic search across all community reports via map-reduce.
    Best for: 'Summarize the main themes', 'What topics recur across documents?'
    Warning: slow (60-120s), no source traceability.
    """
    return await global_search_tool(query)

@mcp.tool()
async def list_entities(entity_type: str | None = None) -> dict:
    """
    List entities in the knowledge graph.
    Optionally filter by type: Person, Organization, Project, Location, etc.
    """
    return await list_entities_tool(entity_type)

@mcp.tool()
async def get_entity(name: str) -> dict:
    """
    Get details and direct relationships for a specific entity by name.
    """
    return await get_entity_tool(name)

# NOTE: sse_app() must be called as a function — missing () is a silent bug
app = mcp.sse_app()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
