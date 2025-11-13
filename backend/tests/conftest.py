"""Pytest fixtures for test setup."""
import pytest
import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture(scope="session", autouse=True)
def setup_test_data():
    """
    테스트 세션 시작 시 자동으로 데이터 ingest 실행.
    
    이미 Qdrant에 데이터가 있으면 스킵하고,
    없으면 ingest.py를 실행하여 테스트용 데이터를 준비합니다.
    """
    import os
    from qdrant_client import QdrantClient
    
    # Qdrant 연결 확인
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    collection = os.getenv("QDRANT_COLLECTION", "qa_collection")
    
    try:
        client = QdrantClient(url=qdrant_url)
        # 컬렉션이 있고 데이터가 있는지 확인
        info = client.get_collection(collection)
        if info.points_count > 0:
            print(f"\n✓ 테스트용 데이터 이미 존재 ({info.points_count}개 포인트)")
            return
    except Exception:
        pass
    
    # 데이터가 없으면 ingest 실행
    print("\n⚙️  테스트용 데이터 ingest 시작...")
    try:
        # ingest.py 임포트 및 실행
        backend_path = Path(__file__).parent.parent
        sys.path.insert(0, str(backend_path))
        
        from ingest import main as ingest_main
        ingest_main()
        print("✓ 테스트용 데이터 ingest 완료")
    except Exception as e:
        print(f"⚠️  Ingest 실패: {e}")
        print("테스트는 계속 진행되지만 일부 테스트가 실패할 수 있습니다.")

