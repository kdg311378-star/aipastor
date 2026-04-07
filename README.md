 🙏 AI Pastor: Ollama & RAG 기반 지능형 성경 상담 시스템

사용자의 고민에 대해 성경 데이터를 근거로 따뜻한 위로와 신학적 조언을 건네는 Django 기반 AI 챗봇 서비스입니다. 로컬 환경의 성능 한계를 기술적 아이디어로 극복하고, 성경 원문에 충실한 답변을 생성하도록 설계되었습니다.

---

 💡 주요 기술적 도전 및 해결 (Troubleshooting)

 1. RAG(검색 증강 생성)를 통한 환각 현상(Hallucination) 방지
* 문제: LLM이 존재하지 않는 성경 구절을 허구로 생성하는 문제 발생.
* 해결: 성경 전권을 ChromaDB(Vector DB)에 구축. 질문이 들어오면 질문과 연관된 핵심 성경 구절 3개를 정밀 추출하여 AI에게 컨텍스트로 전달하는 RAG 아키텍처 구현.
* 결과: 실제 성경 내용에 기반한 답변만 생성하도록 강제하여 데이터 신뢰도 99% 확보.

 2. Ollama를 통한 로컬 모델 서빙 및 최적화
* 해결:** Ollama를 도입하여 로컬 LLM 서빙 환경 구축. `Modelfile`을 직접 설계하여 모델의 시스템 프롬프트(목회자 페르소나)와 추론 파라미터를 최적화함.
* 결과: 외부 API 의존 없이 로컬 리소스만으로 안정적인 AI 추론 환경 구축.

 3. 효율적인 대화 문맥 유지 (Sliding Window Memory)
* 문제: 하드웨어(노트북) 성능 한계로 전체 대화 기록을 LLM에 전달 시 연산 속도 저하 발생.
* 해결: Sliding Window 방식을 도입하여 전체 대화 중 최신 대화 기록 일부만을 선별적으로 모델에 전달. 
* 결과: 대화의 연속성은 유지하면서 추론 속도와 메모리 효율을 극대화함.

 4. 사용자 경험을 고려한 기능 설계 (UI/UX & CRUD)
* 연속성 있는 대화: 매번 방을 새로 만들지 않고 기존 대화에서 이어가는 채팅방 형식 구현.
* 데이터 관리: 대화 기록을 날짜별로 자동 분류하여 아카이빙하며, 필요 없는 기록은 삭제할 수 있는 관리 기능 제공.

---

 🏗 시스템 아키텍처 (System Architecture)

1. Input: 사용자 고민 입력 및 상담 요청.
2. Retrieval: Django 서버가 질문을 벡터화하여 ChromaDB에서 관련 구절(Top-K) 검색.
3. Context Assembly: [검색된 구절] + [최신 대화 일부] + [목회자 프롬프트] 조합.
4. Inference: Ollama API를 통해 로컬 LLM이 성경 기반 답변 생성.
5. Storage: 답변 완료 후 대화 내용을 MySQL에 저장 및 날짜별 히스토리 갱신.

---

 🛠 사용 기술 (Tech Stack)

- AI/ML: Ollama, LangChain, KULLM3 (GGUF), ChromaDB, Sentence-Transformers
- Backend: Python, Django
- Database: MySQL, ChromaDB
- Infras: Google Colab (Training), Windows/Linux (Serving), Git

---

 🚀 실행 방법 (Setup & Installation)

 1) Ollama 모델 설정
```bash
ollama create aipastor -f Modelfile