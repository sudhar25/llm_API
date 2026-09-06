import time
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv
import os
from .auth import create_jwt_token, verify_token
load_dotenv()
from sqlalchemy.orm import Session
from .database import engine, Base, get_db
from . import models
from sqlalchemy import func
from .cache import get_cached_response, set_cached_response

Base.metadata.create_all(bind=engine)



app = FastAPI()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
class LoginData(BaseModel):
    username: str
    password: str
class ChatRequest(BaseModel):
    question: str
    

@app.post("/auth/login")
def login(data: LoginData, db: Session = Depends(get_db)):
    if data.username == "admin" and data.password == "password":
        token = create_jwt_token({"sub": data.username})
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/chat")
def chat(request: ChatRequest, username: str = Depends(verify_token), db: Session = Depends(get_db)):
    cache_key = f"prompt:{request.question.strip().lower()}"
    cached_answer = get_cached_response(cache_key)

    if cached_answer:
        return {
            "user": username,
            "answer": cached_answer,
            "metrics": {"latency_seconds": 0.0, "tokens_used": 0, "source": "cache"}
        }

    start_time = time.time()
    max_retries = 3

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": request.question}
                ],
                timeout=10
            )

            answer = response.choices[0].message.content
            tokens = response.usage.total_tokens if response.usage else 0
            latency = time.time() - start_time

            # Store in Redis cache for 5 minutes
            set_cached_response(cache_key, answer, expiration_seconds=300)

            # Persist metrics to database
            chat_log = models.ChatLog(
                username=username,
                question=request.question,
                answer=answer,
                latency=latency,
                tokens_used=tokens
            )
            db.add(chat_log)
            db.commit()

            return {
                "user": username,
                "answer": answer,
                "metrics": {"latency_seconds": round(latency, 2), "tokens_used": tokens, "source": "llm"}
            }

        except Exception as e:
            if attempt == max_retries - 1:
                raise HTTPException(status_code=503, detail=f"LLM service unavailable: {str(e)}")
            time.sleep(2)
            
@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/metrics")
def get_metrics(db: Session = Depends(get_db)):
    total_requests = db.query(func.count(models.ChatLog.id)).scalar() or 0
    avg_latency = db.query(func.avg(models.ChatLog.latency)).scalar() or 0.0
    total_tokens = db.query(func.sum(models.ChatLog.tokens_used)).scalar() or 0

    return {
        "total_requests": total_requests,
        "average_latency_seconds": round(float(avg_latency), 2),
        "total_tokens_used": int(total_tokens)
    }