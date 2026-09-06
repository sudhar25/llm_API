import time
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from groq import Groq
import os
from .auth import create_jwt_token, verify_token