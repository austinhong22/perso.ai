#!/usr/bin/env python
"""
Qdrant Cloud 마이그레이션 스크립트
로컬 Qdrant 데이터를 Qdrant Cloud로 이전
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import hashlib

# 환경변수 로드
load_dotenv()

def get_local_client():
    """로컬 Qdrant 클라이언트"""
    return QdrantClient(url="http://localhost:6333")

def get_cloud_client():
    """Qdrant Cloud 클라이언트"""
    url = os.getenv("QDRANT_CLOUD_URL")
    api_key = os.getenv("QDRANT_CLOUD_API_KEY")
    
    if not url or not api_key:
        raise ValueError(
            "QDRANT_CLOUD_URL과 QDRANT_CLOUD_API_KEY를 .env에 설정해주세요.\n"
            "Qdrant Cloud에서 Cluster 생성 후:\n"
            "QDRANT_CLOUD_URL=https://xxxxx.cloud.qdrant.io\n"
            "QDRANT_CLOUD_API_KEY=your_api_key"
        )
    
    return QdrantClient(url=url, api_key=api_key)

def migrate_collection(collection_name: str = "qa_collection"):
    """컬렉션 마이그레이션"""
    print(f"🚀 {collection_name} 마이그레이션 시작...\n")
    
    # 1. 로컬 데이터 가져오기
    print("1️⃣ 로컬 Qdrant에서 데이터 읽기...")
    local_client = get_local_client()
    
    try:
        # 컬렉션 정보 가져오기
        collection_info = local_client.get_collection(collection_name)
        vector_size = collection_info.config.params.vectors.size
        print(f"   ✅ 컬렉션 찾음: {collection_name} (벡터 차원: {vector_size})")
        
        # 모든 포인트 가져오기
        points, _ = local_client.scroll(
            collection_name=collection_name,
            limit=1000,
            with_payload=True,
            with_vectors=True
        )
        print(f"   ✅ {len(points)} 개 포인트 읽기 완료\n")
        
    except Exception as e:
        print(f"   ❌ 로컬 데이터 읽기 실패: {e}")
        print("   💡 먼저 로컬에서 'python backend/ingest.py'를 실행하세요.")
        sys.exit(1)
    
    # 2. Qdrant Cloud에 컬렉션 생성
    print("2️⃣ Qdrant Cloud에 컬렉션 생성...")
    cloud_client = get_cloud_client()
    
    try:
        # 기존 컬렉션 삭제 (있다면)
        collections = cloud_client.get_collections().collections
        if any(c.name == collection_name for c in collections):
            print(f"   ⚠️  기존 컬렉션 삭제 중...")
            cloud_client.delete_collection(collection_name)
        
        # 새 컬렉션 생성
        cloud_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            ),
            hnsw_config={
                "m": 16,
                "ef_construct": 100,
                "full_scan_threshold": 10000
            }
        )
        print(f"   ✅ 컬렉션 생성 완료\n")
        
    except Exception as e:
        print(f"   ❌ 컬렉션 생성 실패: {e}")
        sys.exit(1)
    
    # 3. 데이터 업로드
    print("3️⃣ 데이터 업로드 중...")
    
    try:
        # PointStruct로 변환
        cloud_points = []
        for point in points:
            cloud_points.append(
                PointStruct(
                    id=point.id,
                    vector=point.vector,
                    payload=point.payload
                )
            )
        
        # 배치 업로드
        cloud_client.upsert(
            collection_name=collection_name,
            points=cloud_points
        )
        print(f"   ✅ {len(cloud_points)} 개 포인트 업로드 완료\n")
        
    except Exception as e:
        print(f"   ❌ 데이터 업로드 실패: {e}")
        sys.exit(1)
    
    # 4. 검증
    print("4️⃣ 마이그레이션 검증...")
    
    try:
        cloud_info = cloud_client.get_collection(collection_name)
        cloud_count = cloud_info.points_count
        
        if cloud_count == len(points):
            print(f"   ✅ 검증 성공: {cloud_count} 개 포인트")
            print(f"\n🎉 마이그레이션 완료!")
            print(f"\n📋 다음 단계:")
            print(f"   1. Render 대시보드에서 환경변수 설정:")
            print(f"      QDRANT_URL={os.getenv('QDRANT_CLOUD_URL')}")
            print(f"      QDRANT_API_KEY=<your_cloud_api_key>")
            print(f"   2. Backend 배포 진행")
        else:
            print(f"   ⚠️  경고: 포인트 수 불일치 (로컬: {len(points)}, 클라우드: {cloud_count})")
            
    except Exception as e:
        print(f"   ❌ 검증 실패: {e}")
        sys.exit(1)

def test_connection():
    """연결 테스트"""
    print("🔍 Qdrant Cloud 연결 테스트...\n")
    
    try:
        cloud_client = get_cloud_client()
        collections = cloud_client.get_collections()
        print(f"✅ 연결 성공!")
        print(f"📊 기존 컬렉션: {[c.name for c in collections.collections]}\n")
        return True
    except Exception as e:
        print(f"❌ 연결 실패: {e}\n")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Qdrant Cloud 마이그레이션")
    parser.add_argument(
        "--test",
        action="store_true",
        help="연결 테스트만 수행"
    )
    parser.add_argument(
        "--collection",
        default="qa_collection",
        help="마이그레이션할 컬렉션 이름"
    )
    
    args = parser.parse_args()
    
    if args.test:
        test_connection()
    else:
        if test_connection():
            migrate_collection(args.collection)

