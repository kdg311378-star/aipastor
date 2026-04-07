import os
import django
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer

# 1. 장고 환경 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aipastorproject.settings')
django.setup()

from aipastorapp.models import BibleVerse

def build_final_library():
    print("🚀 [1/4] 차원 충돌 방지형 AI 도서관 구축 시작...")
    
    # 2. 임베딩 모델 및 함수 정의 (768차원 고정)
    model_name = "jhgan/ko-sroberta-multitask"
    
    # ★ 핵심: ChromaDB에게 이 모델이 768차원임을 강제로 인지시키는 함수입니다.
    kor_embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model_name)
    
    # 3. ChromaDB 연결
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    
    # 4. ★ 'final' 이라는 새 이름으로 컬렉션 생성
    # 이 과정에서 embedding_function을 인자로 넣어야 384차원으로 변하지 않습니다.
    print("⏳ [2/4] 'bible_final' 컬렉션 생성 중 (768차원 강제 지정)...")
    bible_collection = chroma_client.get_or_create_collection(
        name="bible_final",
        embedding_function=kor_embed_fn
    )
    
    # MySQL에서 성경 데이터 가져오기
    verses = BibleVerse.objects.all()
    if not verses.exists():
        print("❌ 에러: MySQL에 성경 데이터가 없습니다. load_bible.py를 먼저 실행하세요.")
        return

    print(f"⏳ [3/4] 총 {verses.count()}개의 구절을 벡터 DB로 변환 및 저장 중...")
    
    # 데이터 밀어넣기 (100개씩 배치 처리)
    docs, metas, ids = [], [], []
    for i, v in enumerate(verses):
        text = f"{v.book} {v.chapter}:{v.verse} {v.content}"
        docs.append(text)
        metas.append({"book": v.book, "chapter": v.chapter, "verse": v.verse})
        ids.append(str(v.id))
        
        if len(docs) >= 100 or i == len(verses) - 1:
            # embeddings를 직접 계산해서 넣지 않아도 kor_embed_fn이 자동으로 처리합니다.
            bible_collection.add(
                documents=docs,
                metadatas=metas,
                ids=ids
            )
            docs, metas, ids = [], [], []
            if (i + 1) % 500 == 0:
                print(f"   - {i + 1}개 완료...")

    print("🎉 [4/4] 완료! 이제 768차원 전용 도서관이 완성되었습니다.")

if __name__ == "__main__":
    build_final_library()