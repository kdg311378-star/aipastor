from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import ollama
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AI_Server")

app = FastAPI(title="AI Pastor Inference Server (GPU) - Relay Only")

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    temperature: float = 0.6
    num_ctx: int = 2048  # RTX 3060 6GB 메모리 터짐 방지

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

    temperature = float(req.temperature)
    num_ctx = int(req.num_ctx)

    logger.info(f"Incoming Request: {prompt[:80]}...")

    try:
        # 1. Ollama GPU 추론 실행 (이중 껍데기 방지 raw=True)
        resp = ollama.generate(
            model="aipastor",
            prompt=prompt,
            raw=True,
            options={
                "temperature": temperature,
                "num_ctx": num_ctx,
                "stop": ["<|eot_id|>"]  # 이 기호가 나오면 즉시 정지
            }
        )

        # 2. 답변 텍스트 추출
        ai_message = resp.get("response", "")
        
        # 3. ★ 강제 필터링: 화면에 나가기 전에 불순물을 완벽하게 도려냅니다.
        ai_message = ai_message.replace("<|eot_id|>", "").replace("<|begin_of_text|>", "").strip()

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