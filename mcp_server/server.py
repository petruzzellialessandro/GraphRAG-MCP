from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Mount
from mcp_server.tools.local_search import local_search_tool
from mcp_server.tools.basic_search import basic_search_tool
from mcp_server.tools.global_search import global_search_tool
from mcp_server.tools.drift_search import drift_search_tool
from mcp_server.tools.entity_query import list_entities_tool, get_entity_tool

def _with_cors(mcp_app):
    mcp_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return mcp_app


def _build_mcp_app(
    name: str,
    enable_basic: bool,
    enable_local: bool,
    enable_global: bool,
    enable_drift: bool = True,
):
    mcp = FastMCP(name=name)

    if enable_drift:
        @mcp.tool()
        async def drift_search(
            query: str,
            community_level: int = 2,
            response_type: str = "Multiple Paragraphs",
        ) -> dict:
            """
            Entity + Community hybrid search combining local and global insights.
            Best for: 'What are the main consequences of event X across the graph?'
            """
            return await drift_search_tool(
                query,
                community_level=community_level,
                response_type=response_type,
            )

    if enable_local:
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
            return await local_search_tool(
                query,
                community_level=community_level,
                response_type=response_type,
            )

    if enable_basic:
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

    if enable_global:
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

    return _with_cors(mcp.sse_app())


all_search_app = _build_mcp_app(
    name="graphrag-mcp-server-all",
    enable_basic=True,
    enable_local=True,
    enable_global=True,
    enable_drift=True,
)
basic_only_app = _build_mcp_app(
    name="graphrag-mcp-server-basic",
    enable_basic=True,
    enable_local=False,
    enable_global=False,
    enable_drift=False,
)
local_only_app = _build_mcp_app(
    name="graphrag-mcp-server-local",
    enable_basic=False,
    enable_local=True,
    enable_global=False,
    enable_drift=False,
)
global_only_app = _build_mcp_app(
    name="graphrag-mcp-server-global",
    enable_basic=False,
    enable_local=False,
    enable_global=True,
    enable_drift=False,
)
drift_only_app = _build_mcp_app(
    name="graphrag-mcp-server-drift",
    enable_basic=False,
    enable_local=False,
    enable_global=False,
    enable_drift=True,
)

# Default root keeps backward compatibility (/sse => all searches enabled).
app = Starlette(
    routes=[
        Mount("/basic", app=basic_only_app),
        Mount("/local", app=local_only_app),
        Mount("/global", app=global_only_app),
        Mount("/drift", app=drift_only_app),
        Mount("/", app=all_search_app),
    ]
)
