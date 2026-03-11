from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    graphrag_output_dir: str = "./output"
    mcp_host: str = "127.0.0.1"
    mcp_port: int = 8011

    class Config:
        env_file = ".env"
        populate_by_name = True

settings = Settings()
