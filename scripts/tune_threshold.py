import json, numpy as np, os
from pathlib import Path

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

# ---- 프로젝트 설정 (필요 시 값 조정) ----
QDRANT_URL = "http://localhost:6333"
COLLECTION = "qa_collection"
TOP_K = 3
MODEL_NAME = os.getenv("EMBED_MODEL", "snunlp/KR-SBERT-V40K-klueNLI-augSTS")  # ingest.py와 동일 모델
SWEEP_START, SWEEP_END, SWEEP_STEP = 0.75, 0.90, 0.01  # [0.75, 0.89]

# ---- 모델 및 검색 ----
_model = None
def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model

def embed(text: str):
    m = get_model()
    v = m.encode([text], convert_to_numpy=True, normalize_embeddings=True)[0]
    return v.tolist()

def search_topk(qc: QdrantClient, qvec, k=TOP_K):
    res = qc.search(collection_name=COLLECTION, query_vector=qvec, limit=k)
    out = []
    for r in res:
        q = (r.payload or {}).get("question", "")
        out.append((q, float(r.score)))
    return out

# ---- 지표 계산 ----
def compute_metrics(pred_pos_list, labels):
    # labels: exact/para -> Positive, noise -> Negative
    y_true = [0 if lab=="noise" else 1 for lab in labels]
    y_pred = [1 if p else 0 for p in pred_pos_list]

    tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt==1 and yp==1)
    fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt==0 and yp==1)
    fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt==1 and yp==0)

    precision = tp / (tp + fp + 1e-9)
    recall    = tp / (tp + fn + 1e-9)
    f1        = 2*precision*recall / (precision+recall + 1e-9)
    return precision, recall, f1

def main():
    # 1) 평가 세트 로드
    items = [json.loads(l) for l in Path("eval_set.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    queries = [it["query"] for it in items]
    labels  = [it["label"] for it in items]
    
    print(f"=== 평가 세트: {len(items)}개 쿼리 (exact/para: {sum(1 for l in labels if l!='noise')}, noise: {sum(1 for l in labels if l=='noise')}) ===\n")

    # 2) 쿼리별 Top-1 점수 수집
    qc = QdrantClient(url=QDRANT_URL)
    top1_scores = []
    print("검색 중...")
    for q in queries:
        hits = search_topk(qc, embed(q), k=TOP_K)
        s = hits[0][1] if hits else 0.0
        top1_scores.append(s)
    print(f"검색 완료.\n")

    # 3) 임계값 스윕
    results = []
    Ts = np.arange(SWEEP_START, SWEEP_END, SWEEP_STEP)
    for T in Ts:
        pred_pos = [s >= T for s in top1_scores]  # score >= T => Positive(데이터셋에 있음)
        p, r, f1 = compute_metrics(pred_pos, labels)
        results.append((float(T), p, r, f1))

    # 4) 최적 T (F1 최대) 선택 및 출력
    best = max(results, key=lambda x: x[3])
    print("=== Threshold Sweep ===")
    for T, p, r, f1 in results:
        marker = " <-- Best" if abs(T - best[0]) < 0.001 else ""
        print(f"T={T:.2f}  P={p:.3f}  R={r:.3f}  F1={f1:.3f}{marker}")
    print(f"\n>>> Best: T={best[0]:.2f}, P={best[1]:.3f}, R={best[2]:.3f}, F1={best[3]:.3f}")

    # 5) README에 붙일 요약 파일
    Path("tune_report.json").write_text(
        json.dumps({
            "sweep":[{"T":T,"precision":p,"recall":r,"f1":f1} for T,p,r,f1 in results],
            "best":{"T":best[0],"precision":best[1],"recall":best[2],"f1":best[3]}
        }, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print("\nSaved: tune_report.json")

if __name__ == "__main__":
    main()

