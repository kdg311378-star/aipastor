from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
import requests
from django.forms import modelform_factory
from .models import FaithProfile, ChatSession, ChatMessage, BibleVerse
from django.contrib.auth import logout 
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.core.paginator import Paginator

# ==========================================
# ★ [핵심 1] 듀얼 벡터 DB 세팅 (초기화 완료)
# ==========================================
# aipastorapp/views.py 상단

from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer, util
import chromadb

# 2. 전역 변수 미리 선언 (NameError 방지: try 블록 실패해도 변수는 존재하게 함)
embed_model = None
bible_collection = None
memory_collection = None
ANCHOR_KNOWLEDGE = None
ANCHOR_COUNSELING = None

try:
    print("⏳ [시스템] 768차원 최적화 모델 및 벡터 DB 로드 중...")
    model_name = "jhgan/ko-sroberta-multitask"
    embed_model = SentenceTransformer(model_name)
    
    # ChromaDB 768차원 강제 지정 함수
    kor_embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model_name)
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    
    # ★ 서랍 이름을 'final'로 고정해서 과거 384차원 찌꺼기 무시
    bible_collection = chroma_client.get_or_create_collection(
        name="bible_final", 
        embedding_function=kor_embed_fn
    )
    memory_collection = chroma_client.get_or_create_collection(
        name="memory_final", 
        embedding_function=kor_embed_fn
    )
    
    # 3. 의도 분류용 기준값 (NameError: ANCHOR_KNOWLEDGE 방지)
    ANCHOR_KNOWLEDGE = embed_model.encode("예수님 실존 역사적 증거 교리 성경 해석 삼위일체 이단")
    ANCHOR_COUNSELING = embed_model.encode("너무 우울하고 슬퍼요 인간관계 때문에 힘들고 위로가 필요해요 막막함")
    
    print("✅ [성용님 확인] 모든 시스템이 정상적으로 초기화되었습니다.")

except Exception as e:
    print("❌ [치명적 에러] 초기화 실패. 원인 분석이 필요합니다:")
    traceback.print_exc()

BIBLE_ORDER = [
    '창세기', '출애굽기', '레위기', '민수기', '신명기', '여호수아', '사사기', '룻기',
    '사무엘상', '사무엘하', '열왕기상', '열왕기하', '역대상', '역대하', '에스라', '느헤미야',
    '에스더', '욥기', '시편', '잠언', '전도서', '아가', '이사야', '예레미야', '예레미야애가',
    '에스겔', '다니엘', '호세아', '요엘', '아모스', '오바댜', '요나', '미가', '나훔', '하박국',
    '스바냐', '학개', '스가랴', '말라기', 
    '마태복음', '마가복음', '누가복음', '요한복음', '사도행전', '로마서', '고린도전서', '고린도후서',
    '갈라디아서', '에베소서', '빌립보서', '골로새서', '데살로니가전서', '데살로니가후서',
    '디모데전서', '디모데후서', '디도서', '빌레몬서', '히브리서', '야고보서',
    '베드로전서', '베드로후서', '요한일서', '요한이서', '요한삼서', '유다서', '요한계시록'
]

# ==========================================
# 기본 화면 및 회원가입
# ==========================================
def signup(request):
    ProfileForm = modelform_factory(FaithProfile, fields=['faith_stage'])
    if request.method == 'POST':
        user_form = UserCreationForm(request.POST) 
        profile_form = ProfileForm(request.POST)   
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            login(request, user)
            return redirect('main_page')
    else:
        return render(request, 'registration/signup.html', {'user_form': UserCreationForm(), 'profile_form': ProfileForm()})

def force_logout_login(request):
    if request.user.is_authenticated:
        logout(request)
    return LoginView.as_view(template_name='registration/login.html')(request)

@login_required
def main_page(request):
    return render(request, 'main.html')

@login_required
def chat_page(request):
    profile, _ = FaithProfile.objects.get_or_create(user=request.user, defaults={'faith_stage': '초신자'})
    sessions = ChatSession.objects.filter(user=request.user).order_by('-created_at')
    selected_session_id = request.GET.get('session_id')
    past_messages = ChatMessage.objects.filter(session__session_id=selected_session_id, session__user=request.user).order_by('created_at') if selected_session_id else []
    
    return render(request, 'chat.html', {'user': request.user, 'profile': profile, 'sessions': sessions, 'past_messages': past_messages, 'selected_session_id': selected_session_id})

# ==========================================
# 벡터 RAG 및 의도 분류
# ==========================================
def _retrieve_verses_vector(user_message: str, k: int = 3):
    if not bible_collection: return []
    results = bible_collection.query(query_embeddings=embed_model.encode([user_message]).tolist(), n_results=k)
    return [f"{m['content']} ({m['book']} {m['chapter']}:{m['verse']})" for m in results['metadatas'][0]] if results and results['metadatas'] else []

def _classify_intent_vector(user_message: str) -> bool:
    if not embed_model: return False
    query_vec = embed_model.encode(user_message)
    return util.cos_sim(query_vec, ANCHOR_KNOWLEDGE).item() > util.cos_sim(query_vec, ANCHOR_COUNSELING).item() and util.cos_sim(query_vec, ANCHOR_KNOWLEDGE).item() > 0.4

# ==========================================
# ★ [핵심 2] 채팅 API (환각 없는 완벽 기억력 + VRAM 하드 캡)
# ==========================================
@csrf_exempt
@login_required
def chat_api(request):
    if request.method != "POST": return JsonResponse({"response": "잘못된 요청"}, status=400)

    try:
        data = json.loads(request.body)
        user_message = (data.get("message") or "").strip()
        client_session_id = data.get("session_id")

        if not user_message: return JsonResponse({"response": "메시지 없음"}, status=400)

        session = ChatSession.objects.filter(session_id=client_session_id, user=request.user).first() if client_session_id else ChatSession.objects.create(user=request.user, title=user_message[:20] + "...")
        user_msg_obj = ChatMessage.objects.create(session=session, sender="USER", message=user_message)
        
        profile = FaithProfile.objects.filter(user=request.user).first()
        faith_stage = profile.faith_stage if profile else "초신자"

        # --- 1단계: 과거 기억 불러오기 (텍스트 200자 강제 절단 + 유사도 커트라인 적용) ---
        past_memory_text = ""
        if memory_collection:
            mem_results = memory_collection.query(
                query_embeddings=embed_model.encode([user_message]).tolist(),
                n_results=2, 
                where={"session_id": str(session.session_id)},
                include=["documents", "distances"] # 거리(유사도) 계산 포함
            )
            
            if mem_results and mem_results['documents'] and len(mem_results['documents'][0]) > 0:
                valid_memories = []
                for i, doc in enumerate(mem_results['documents'][0]):
                    distance = mem_results['distances'][0][i]
                    # 거리가 1.0 미만인(관련도 높은) 기억만 쏙쏙 뽑아오기
                    if distance < 1.0: 
                        # 아무리 길어도 200자에서 싹둑 잘라서 VRAM 폭발 방지
                        valid_memories.append(doc[:200] + "...") 
                
                if valid_memories:
                    past_memory_text = "\n".join(valid_memories)

        # --- 2단계: 성경 구절 검색 (성용님 논리대로 k=3 유지해서 퀄리티 방어) ---
        knowledge_mode = _classify_intent_vector(user_message)
        retrieved = _retrieve_verses_vector(user_message, k=3)
        
        # --- ★ 날아갔던 허리 부분 복구: sys_inst 정의 ---
        if knowledge_mode:
            sys_inst = f"당신은 해설 목사입니다. 신앙 단계: {faith_stage}.\n[참고 구절]\n{chr(10).join(retrieved)}"
        else:
            sys_inst = f"당신은 공감 코칭 목사입니다. 신앙 단계: {faith_stage}.\n[오늘의 말씀]\n{retrieved[0] if retrieved else '시편 34:18'}"

        # --- 3단계: 최종 프롬프트 격리벽 조립 (특수 태그 제거) ---
        memory_block = f"\n[과거 대화 참고용]\n{past_memory_text}\n(※ 주의: 위 내용은 이전 대화일 뿐입니다. 새로운 질문에만 집중하세요.)\n" if past_memory_text else ""
        
        # Ollama가 자체적으로 템플릿을 씌우도록, 순수 텍스트로만 구조화!
        prompt = f"[{sys_inst}]\n{memory_block}\n[성도의 질문]\n{user_message}\n\n위 질문에 대해 목사님으로서 따뜻하고 명확한 답변을 작성해주세요:"

        # --- 4단계: AI 서버(FastAPI) 호출 ---
        resp = requests.post("http://localhost:8001/chat", json={"message": prompt, "temperature": 0.6, "num_ctx": 2048}, timeout=120)
        
        if resp.status_code == 200:
            ai_response = resp.json().get("response", "").strip()
            ChatMessage.objects.create(session=session, sender="AI", message=ai_response)
            
            # --- 5단계: 현재 나눈 대화를 벡터 DB에 저장 ---
            if memory_collection:
                chunk = f"Q: {user_message}\nA: {ai_response}"
                memory_collection.add(
                    documents=[chunk],
                    metadatas=[{"session_id": str(session.session_id)}],
                    ids=[str(user_msg_obj.message_id)] 
                )
            
            return JsonResponse({"response": ai_response, "session_id": session.session_id})
        else:
            user_msg_obj.delete()
            return JsonResponse({"response": "AI 서버 오류"}, status=500)

    except Exception as e:
        # ★ 에러 민낯 까발리기용 터미널 출력 유지
        import traceback
        print("🚨 [백엔드 에러 발생] 🚨")
        traceback.print_exc()
        return JsonResponse({"response": f"서버 내부 에러: {str(e)}"}, status=500)

@csrf_exempt
@login_required
def delete_last_message(request):
    if request.method == "POST":
        data = json.loads(request.body)
        if session_id := data.get("session_id"):
            last_msg = ChatMessage.objects.filter(session__session_id=session_id, sender="USER").order_by('-created_at').first()
            if last_msg: last_msg.delete()
        return JsonResponse({"status": "deleted"})
    return JsonResponse({"status": "error"})

# ==========================================
# ★ [핵심 3] 기록 삭제 시 유령 기억(Ghost Memory) 완벽 삭제 동기화
# ==========================================
@login_required
def delete_chat_session(request, session_id):
    if request.method == 'POST':
        get_object_or_404(ChatSession, session_id=session_id, user=request.user).delete()
        if memory_collection: memory_collection.delete(where={"session_id": str(session_id)})
    return redirect('chat_history')

@login_required
def delete_selected_chat_history(request):
    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_sessions')
        if selected_ids:
            ChatSession.objects.filter(session_id__in=selected_ids, user=request.user).delete()
            if memory_collection:
                for sid in selected_ids: memory_collection.delete(where={"session_id": str(sid)})
    return redirect('chat_history')

@login_required
def delete_all_chat_history(request):
    if request.method == 'POST':
        session_ids = list(ChatSession.objects.filter(user=request.user).values_list('session_id', flat=True))
        ChatSession.objects.filter(user=request.user).delete()
        if memory_collection and session_ids:
            for sid in session_ids: memory_collection.delete(where={"session_id": str(sid)})
    return redirect('chat_history')

# ==========================================
# 성경 검색 및 채팅 기록 관리
# ==========================================
@login_required
def bible_search(request):
    query = request.GET.get('q', '').strip()
    selected_book = request.GET.get('book', '')
    selected_chapter = request.GET.get('chapter', '')
    
    chapter_list = []
    verses = []
    
    if selected_book:
        chapter_list = BibleVerse.objects.filter(book=selected_book).values_list('chapter', flat=True).distinct().order_by('chapter')

    if selected_book and selected_chapter:
        verses = BibleVerse.objects.filter(book=selected_book, chapter=selected_chapter).order_by('verse')
    elif query:
        title_matches = BibleVerse.objects.filter(book__icontains=query).order_by('id')
        content_matches = BibleVerse.objects.filter(content__icontains=query).exclude(id__in=title_matches).order_by('id')
        verses = list(title_matches) + list(content_matches)

    page_obj = None
    total_count = 0
    
    if verses:
        if isinstance(verses, list):
            total_count = len(verses)
        else:
            total_count = verses.count()
        
        if selected_book and selected_chapter:
            page_obj = verses 
        else:
            paginator = Paginator(verses, 10) 
            page = request.GET.get('page', '1')
            page_obj = paginator.get_page(page)

    context = {
        'bible_list': BIBLE_ORDER,
        'selected_book': selected_book,
        'selected_chapter': int(selected_chapter) if selected_chapter else None,
        'chapter_list': chapter_list,
        'verses': page_obj if (not selected_chapter) else verses,
        'is_chapter_view': bool(selected_book and selected_chapter),
        'query': query,
        'total_count': total_count,
    }
    return render(request, 'bible_search.html', context)

@login_required
def chat_history(request):
    sessions = ChatSession.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'history.html', {'sessions': sessions})