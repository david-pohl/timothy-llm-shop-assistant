from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import mysql.connector

from requests import post
import json


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Replace with your frontend's origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="db",
        database="mysql"
    )

class Message(BaseModel):
    text: str



@app.get("/check")
async def check():
    return {
        "status": "ok"
    }

@app.post("/send/message")
async def send_message(msg: Message):
    print(msg.text)

    response_text = ""
    for chunk in post(
        url="http://localhost:11434/api/generate", 
        json={
            "model": "llama3.2:3b",
            "prompt": msg.text
        }).text.splitlines():
        response_text += json.loads(chunk)["response"]

    print(response_text)
    return {"message": response_text}
