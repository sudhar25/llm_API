from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from .database import Base

class ChatLog(Base):
    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    question = Column(String)
    answer = Column(String)
    latency = Column(Float)
    tokens_used = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())