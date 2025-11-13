# Qdrant 컬렉션 버저닝 가이드

## 개요
임베딩 모델/파라미터 변경 시 컬렉션 버전을 관리하는 전략 문서.

## 버전 관리 정책

### 버전 네이밍 규칙
```
qa_collection_v{VERSION}
```
- `v1`: 초기 버전 (snunlp/KR-SBERT-V40K-klueNLI-augSTS, COSINE, 768d)
- `v2`: 모델 변경 시
- `v3`: 파라미터 최적화 시

### 환경 변수
```bash
QDRANT_COLLECTION=qa_collection_v1
COLLECTION_VERSION=v1
EMBED_MODEL=snunlp/KR-SBERT-V40K-klueNLI-augSTS
EMBED_DIM=768
```

## 마이그레이션 절차

### 1. 새 버전 생성
```bash
# 환경 변수 업데이트
QDRANT_COLLECTION=qa_collection_v2
COLLECTION_VERSION=v2
EMBED_MODEL=new-model-name

# 데이터 재인덱싱
python backend/ingest.py
```

### 2. 백엔드 전환
```bash
# app.py / config.py의 컬렉션명 변경 후 재시작
uvicorn backend.app:app --reload
```

### 3. A/B 테스트
```python
# 두 버전 동시 쿼리 후 비교
client_v1 = QdrantClient(...).search("qa_collection_v1", ...)
client_v2 = QdrantClient(...).search("qa_collection_v2", ...)
```

### 4. 구버전 삭제
```python
client.delete_collection("qa_collection_v1")
```

## 버전 이력

| Version | Model | Dim | HNSW (m, ef) | Date | Notes |
|---------|-------|-----|--------------|------|-------|
| v1 | snunlp/KR-SBERT-V40K-klueNLI-augSTS | 768 | 16, 100 | 2025-01-13 | 초기 배포 + HNSW 최적화 |

## 롤백 절차
```bash
# 환경 변수를 이전 버전으로 복원
QDRANT_COLLECTION=qa_collection_v1
COLLECTION_VERSION=v1

# 서버 재시작
pkill -f uvicorn
python backend/app.py
```

## 모니터링 체크리스트
- [ ] 평균 검색 latency (< 100ms)
- [ ] 캐시 hit rate
- [ ] 임계값 통과율 (Recall)
- [ ] 할루시네이션 발생률 (= 0)


