from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    qdrant_url: str = Field(default="http://localhost:6333", validation_alias="QDRANT_URL")
    qdrant_collection: str = Field(default="qa_collection", validation_alias="QDRANT_COLLECTION")
    embed_dim: int = Field(default=768, validation_alias="EMBED_DIM")  # ko-sroberta-multitask 차원
    sim_threshold: float = Field(default=0.83, validation_alias="SIM_THRESHOLD")
    top_k: int = Field(default=3, validation_alias="TOP_K")

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()


