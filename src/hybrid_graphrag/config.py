from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')
    
    # OpenAI
    openai_api_key: str = Field(default="")
    
    # OpenAlex
    openalex_api_key: str = Field(default="")
    openalex_email: str = Field(default="")
    
    # Neo4j
    neo4j_uri: str = Field(default="bolt://localhost:7687")
    neo4j_username: str = Field(default="neo4j")
    neo4j_password: str = Field(default="password")
    
    # Qdrant
    qdrant_url: str = Field(default="http://localhost:6333")
    qdrant_api_key: str = Field(default="")
    
    # App
    log_level: str = Field(default="INFO")
    
    # Settings
    data_dir: str = Field(default="data")

settings = Settings()
