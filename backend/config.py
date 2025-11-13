from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    qdrant_url: str = Field(default="http://localhost:6333", validation_alias="QDRANT_URL")
    qdrant_collection: str = Field(default="qa_collection", validation_alias="QDRANT_COLLECTION")
    embed_model: str = Field(default="snunlp/KR-SBERT-V40K-klueNLI-augSTS", validation_alias="EMBED_MODEL")
    embed_dim: int = Field(default=768, validation_alias="EMBED_DIM")
    sim_threshold: float = Field(default=0.75, validation_alias="SIM_THRESHOLD")
    top_k: int = Field(default=3, validation_alias="TOP_K")

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()


