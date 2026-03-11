import uvicorn
from mcp_server.server import app
from core.config import settings

if __name__ == "__main__":
    uvicorn.run(app, host=settings.mcp_host, port=settings.mcp_port)
