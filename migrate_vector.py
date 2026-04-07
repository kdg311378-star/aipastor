import os
import django

# 1. Django 환경 세팅 (유저님의 실제 프로젝트 이름인 aipastorproject 반영)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aipastorproject.settings")
django.setup()

# 2. 유저님의 실제 앱 이름인 aipastorapp 반영
from aipastorapp.models import BibleVerse
import chromadb
from sentence_transformers import SentenceTransformer

def run_migration():
    print("⏳ 1. 한국어 임베딩 모델을 다운로드합니다... (최초 1회, 약간의 시간 소요)")
    embed_model = SentenceTransformer('jhgan/ko-sroberta-multitask')

    print("⏳ 2. Vector DB(Chroma) 저장소를 생성합니다...")
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    
    try:
        chroma_client.delete_collection(name="bible_collection")
    except Exception:
        pass
    
    collection = chroma_client.create_collection(name="bible_collection")

    print("⏳ 3. SQLite DB에서 성경 데이터를 읽어옵니다...")
    verses = BibleVerse.objects.all()
    total_verses = verses.count()
    print(f"✅ 총 {total_verses}개의 성경 구절이 확인되었습니다.")

    if total_verses == 0:
        print("❌ 성경 데이터가 비어있습니다. 기존 DB에 성경 데이터가 있는지 확인해주세요.")
        return

    batch_size = 500  
    print(f"🚀 4. 의미(벡터) 변환 및 Vector DB 저장을 시작합니다. (PC 사양에 따라 2~5분 소요)")
    
    texts = []
    metadatas = []
    ids = []

    for i, v in enumerate(verses):
        texts.append(v.content)
        metadatas.append({
            "book": v.book,
            "chapter": v.chapter,
            "verse": v.verse,
            "content": v.content
        })
        ids.append(str(v.id))

        if len(texts) >= batch_size or i == total_verses - 1:
            embeddings = embed_model.encode(texts).tolist()
            
            collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            print(f"   -> 변환 진행률: {i+1} / {total_verses} 완료")
            
            texts = []
            metadatas = []
            ids = []

    print("🎉 [성공] 모든 성경 데이터가 의미 기반 Vector DB로 완벽하게 이주되었습니다!")

if __name__ == "__main__":
    run_migration()