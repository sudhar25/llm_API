import time
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv
import os
from .auth import create_jwt_token, verify_token

load_dotenv()

app = FastAPI()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
class LoginData(BaseModel):
    username: str
    password: str
class ChatRequest(BaseModel):
    question: str
    

@app.post("/auth/login")
def login(data: LoginData):
    if data.username == "admin" and data.password == "password":
        token = create_jwt_token({"sub": data.username})
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/chat")
def chat(request: ChatRequest, username: str = Depends(verify_token)):
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
            
            return {
                "user": username,
                "answer": answer,
                "metrics": {"latency_seconds": round(latency, 2), "tokens_used": tokens}
            }
            
        except Exception as e:
            if attempt == max_retries - 1:
                raise HTTPException(status_code=503, detail=f"LLM service unavailable: {str(e)}")
            time.sleep(2)
            
@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/metrics")
def metrics():
    return {"total_requests": 150, "average_latency": 1.2}