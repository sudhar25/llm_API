import time
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from groq import Groq
import os
from .auth import create_jwt_token, verify_token

app = FastAPI()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
class LoginData(BaseModel):
    username: str
    password: str
class ChatRequest(BaseModel):
    question: str