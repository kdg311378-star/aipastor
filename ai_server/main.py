# main.py (중계기/추론 전용 최종본)
# ✅ Django가 "프롬프트+DB근거(구절)"까지 다 만들어서 message로 보내는 전제
# ✅ FastAPI는 DB/룰/프롬프트 생성 절대 안 함 (추론만)
# ✅ history/use_history 같은 거 싹 무시 가능(요청 와도 기본은 1턴)
# ✅ response에서 불필요한 메타/규칙 누수 최소화
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import ollama
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AI_Server")

app = FastAPI(title="AI Pastor Inference Server (GPU) - Relay Only")


class ChatRequest(BaseModel):
    # ✅ Django에서 만들어 보낸 "완성 프롬프트"가 여기에 들어옴
    message: str = Field(..., min_length=1)

    # 옵션(있어도 됨)
    temperature: float = 0.7
    num_ctx: int = 4096


@app.get("/health")
async def health_check():
    try:
        ollama.list()
        return {"status": "online", "gpu_backend": "ollama"}
    except Exception as e:
        logger.error(f"Health Check Failed: {e}")
        raise HTTPException(status_code=503, detail="Ollama engine is unreachable")


@app.post("/chat")
async def chat(req: ChatRequest):
    start_time = time.time()
    prompt = (req.message or "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="message is empty")

    # temperature: Django에서 지식형이면 0.0, 상담형이면 0.6 같은 식으로 내려보내면 됨
    temperature = float(req.temperature)
    num_ctx = int(req.num_ctx)

    logger.info(f"Incoming Request: {prompt[:80]}...")

    try:
        # ✅ 여기서 system/user를 추가하지 않는다.
        # Django가 이미 "### System: ... ### User: ... ### Assistant:" 형태로 프롬프트를 만들어 보내는 전제.
        resp = ollama.chat(
            model="aipastor",
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": temperature,
                "num_ctx": num_ctx,
            },
        )

        ai_message = (resp.get("message", {}) or {}).get("content", "")
        process_time = round(time.time() - start_time, 2)

        logger.info(f"Response Generated in {process_time}s (temp={temperature}, num_ctx={num_ctx})")

        return {
            "response": ai_message,
            "processing_time": process_time,
            "model": "aipastor-gpu-v1",
        }

    except Exception as e:
        logger.error(f"Inference Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
