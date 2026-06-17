import os
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    mongodb_uri: str = Field(default="mongodb://localhost:27017")
    database_name: str = Field(default="repomind")

    gemini_api_key: str = Field(default="")

    qdrant_url: str = Field(default="http://localhost:6333")
    qdrant_host: str = Field(default="localhost")
    qdrant_port: int = Field(default=6333)
    qdrant_in_memory: bool = Field(default=True)

    repos_cache_dir: str = Field(default="./cache/repos")

    jwt_secret: str = Field(default="supersecretjwtsecretkeyrepomindai2026")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=1440)

    model_config = {
        "env_file": os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

settings = Settings()
