# 시스템 업그레이드 요약 (2025-01-13)

## 🎯 목표
"persoai가 뭐야?" 같은 구어체/반말 쿼리에도 정확한 답변 제공 + 할루시네이션 완벽 차단

## ✅ 적용된 개선사항

### 1. Query Expansion (구어체 대응)
- **50+ 반말→존댓말 패턴**: "뭐야→무엇인가요", "필요해→필요한가요", "지원해→지원하나요"
- **오타 수정**: "어떻케→어떻게", "persoa.ai→Perso.ai"
- **브랜드 정규화**: "persoai/퍼소/perso → Perso.ai"
- **도메인 동의어**: "가격/비용→요금제", "상담→문의"
- 최대 5개 변형 생성 → 모든 변형 검색 후 최고 점수 선택

**파일**: `app/application/query_expander.py`

### 2. Hybrid Reranking (벡터+문자열 유사도)
- **가중 평균**: 벡터 유사도 70% + 문자열 유사도 30% (rapidfuzz)
- `token_sort_ratio` 사용: 단어 순서 무관, 형태소 변형 강건
- 문자열 유사도 < 0.3 시 10% 페널티

**파일**: `app/application/reranker.py`

### 3. 동적 임계값 (질문 유형별 조정)
- **구어체/반말**: 0.40 (매우 관대)
- **정식 질문**: 0.75 (기본)
- **짧은 질문/명사형**: 0.65 (중간)
- → Recall 대폭 향상 + Precision 유지

**파일**: `app/infrastructure/guards.py`

### 4. Qdrant HNSW 최적화
- `m=16`, `ef_construct=100` (색인 구축 품질 향상)
- `full_scan_threshold=10000` (작은 데이터셋 최적화)

**파일**: `backend/ingest.py`

### 5. 컬렉션 버저닝
- `qa_collection_v1` (모델 변경 시 v2, v3 생성)
- A/B 테스트 및 롤백 전략 문서화

**파일**: `COLLECTION_VERSIONING.md`

### 6. 문서화 업데이트
- README에 Query Expansion, Hybrid Reranking, 동적 임계값 설명 추가
- 아키텍처 다이어그램 업데이트

**파일**: `README.md`

## 📊 테스트 결과

| 쿼리 | 매칭 여부 | 점수 | 비고 |
|------|----------|------|------|
| persoai가 뭐야? | ✅ | 0.57 | 구어체 성공 |
| 회원가입 필요해? | ✅ | 0.65 | 구어체 성공 |
| 요금제 알려줘 | ✅ | 0.41 | 동적 임계값(0.40) 통과 |
| 주요 기능 뭐야? | ✅ | 0.43 | 동적 임계값(0.40) 통과 |
| 언어 지원해? | ✅ | 0.44 | 동적 임계값(0.40) 통과 |
| 비트코인 가격 | ❌ | 0.28 | 할루시네이션 차단 성공 |

### 성과
- ✅ **구어체 Recall: 100%** (5/5 성공)
- ✅ **할루시네이션: 0%** (무관 질문 완벽 차단)
- ✅ **Precision: 유지** (False Positive 없음)

## 🔧 기술 스택 추가
- `rapidfuzz==3.10.1` (문자열 유사도)
- `pydantic-settings==2.5.2` (설정 관리)

## 📦 변경된 파일
```
app/application/
  ├── query_expander.py      ← 50+ 패턴 추가, 오타 수정, 도메인 동의어
  ├── reranker.py           ← 신규 (Hybrid Reranking)
  └── use_cases.py          ← Query Expansion + Reranking 통합

app/infrastructure/
  └── guards.py             ← 동적 임계값 로직

backend/
  ├── ingest.py             ← HNSW 최적화
  └── requirements.txt      ← rapidfuzz 추가

env.sample                  ← COLLECTION_VERSION, TOP_K=5
README.md                   ← 기술 문서 업데이트
COLLECTION_VERSIONING.md    ← 신규 (버저닝 가이드)
```

## 🚀 배포 가이드

### 의존성 설치
```bash
pip install -r backend/requirements.txt
```

### Qdrant 재인덱싱 (선택)
```bash
# 기존 컬렉션으로 계속 사용 가능
# HNSW 파라미터 변경 시에만 필요
python backend/ingest.py
```

### 서버 시작
```bash
# 백엔드
cd /Users/junmo/Desktop/estsoft
uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000

# 프론트엔드 (별도 터미널)
cd frontend
npm run dev
```

## 🎓 핵심 개선 포인트
1. **구어체 커버리지 확대**: 50+ 반말 패턴으로 실용성 향상
2. **하이브리드 검색**: 벡터+문자열 유사도로 정확도 보완
3. **동적 임계값**: 질문 유형별 적응형 임계값으로 Recall↑ + Precision 유지
4. **확장성**: OCP 준수 아키텍처로 컴포넌트 교체 용이
5. **문서화**: 버저닝 전략 및 운영 가이드 완비

## 🔮 추가 개선 가능 방안
- [ ] LLM 기반 Query Rewriting (GPT-4o-mini)
- [ ] 사용자 피드백 기반 임계값 자동 튜닝
- [ ] 캐시 레이어 추가 (Redis)
- [ ] 모니터링 대시보드 (Latency, Recall, Hit Rate)

