from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from config import settings


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[str]


app = FastAPI(title="ESTSOFT RAG API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/search", response_model=QueryResponse)
async def search(req: QueryRequest):
    # STEP 0: placeholder 응답 (유사도 미달 가드 메시지)
    return QueryResponse(
        answer="죄송해요, 제가 가지고 있는 데이터셋에는 해당 내용이 없어요.",
        sources=[],
    )


