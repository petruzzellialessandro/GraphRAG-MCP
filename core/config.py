from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    openai_api_key: str = ""
    graphrag_output_dir: str = "./output"
    mcp_host: str = "127.0.0.1"
    mcp_port: int = 8011

    class Config:
        env_file = ".env"

settings = Settings()
