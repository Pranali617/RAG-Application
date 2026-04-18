import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Get the absolute path of the directory where this file is located (src/)
# Then go one level up to the project root where .env lives
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = os.path.join(BASE_DIR, ".env")

class Settings(BaseSettings):
    # Variables with defaults
    ES_URL: str = "http://localhost:9200"
    ES_INDEX: str = "pdf_search_index"
    FILE_EXT_ALLOWED: list = [".pdf",".PDF"]
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # Required variables (will error if not in .env)
    GOOGLE_API_KEY: str
    MODEL_NAME: str
    APP_NAME: str
    CHUNK_SIZE :int= 1000
    CHUNK_OVERLAP :int= 100
    # Explicitly point to the absolute path of .env
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore"
    )

Config = Settings()