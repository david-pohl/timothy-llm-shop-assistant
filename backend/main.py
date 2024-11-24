from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import mysql.connector

from requests import post
import json
from typing import List

from tqdm import tqdm


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Replace with your frontend's origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)


PROMPT_SYSTEM = """\
You are Timothy, an AI assistant specialized in generating SQL queries for an online clothing retail inventory system. \
Based on user requests, return only the SQL query that satisfies their query. \
If you cannot confidently create an SQL query to address the request, respond with 'None'. Do not include any explanations, comments, or additional details in your responses.\
"""

PROMPT_USER = """You are part of an 
"""

PROMPT_INTERNAL = """\
Given the following user question, corresponding SQL query, and SQL result, answer the user question.

Question: {question};
SQL Query: {query};
SQL Result: {result};
Answer: \
"""

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="db",
        database="mysql"
    )

def init_db():
    prod_cols = ["id", "name", "sku", "parent", "price", "stock", "img", "text", "bullets"]
    prod_sql = f"""INSERT INTO products ({", ".join(prod_cols)}) VALUES ({", ".join(["%s"] * len(prod_cols))})"""
    
    size_cols = ["product_id", "size"]
    size_sql = f"""INSERT INTO sizes ({", ".join(size_cols)}) VALUES ({", ".join(["%s"] * len(size_cols))})"""
    
    cat_cols = ["product_id", "category"]
    cat_sql = f"""INSERT INTO categories ({", ".join(cat_cols)}) VALUES ({", ".join(["%s"] * len(cat_cols))})"""
    
    with open("data/scraped_2024_11_24_13_17_36.json", "r") as f:
        scraped_items = json.load(f) 
        prod_vals, size_vals, cat_vals = [], [], []
        for item in tqdm(scraped_items):
            prod_vals.append(tuple([item[col] if col != "price" else item["price ($)"] for col in prod_cols]))
            for size in item["size"]:
                size_vals.append((item["id"], size))

            cats = set()
            for category in item["categories"]:
                for level in category:
                    if level not in cats:
                        cat_vals.append((item["id"], level))
                        cats.add(level)

    connection = get_db_connection()

    with connection.cursor() as cursor:
        with open("data/init_table_products.sql", "r") as f:
            sql = f.read()
            cursor.execute(sql)
        with open("data/init_table_sizes.sql", "r") as f:
            sql = f.read()
            cursor.execute(sql)
        with open("data/init_table_categories.sql", "r") as f:
            sql = f.read()
            cursor.execute(sql)
        
        connection.commit()

    with connection.cursor() as cursor:
        cursor.executemany(prod_sql, prod_vals)
        cursor.executemany(size_sql, size_vals)  
        cursor.executemany(cat_sql, cat_vals)

        connection.commit()

    connection.close()

init_db()


class Message(BaseModel):
    sender: str
    text: str


@app.get("/check")
async def check():
    return {
        "status": "ok"
    }

@app.post("/send/message")
async def send_message(messages: List[Message]):
    system_message = {
        "role": "system",
        "content": PROMPT_SYSTEM
    }

    chat_messages = [
        {
            "role": "assistant" if m.sender == "Timothy" else "user",
            "content": m.text
        } 
        for m in messages
    ]
    print([system_message] + chat_messages)

    response_text = ""
    for chunk in post(
        url="http://localhost:11434/api/chat", 
        json={
            "model": "llama3.2:3b",
            "messages": [system_message] + chat_messages
        }).text.splitlines():
        response_text += json.loads(chunk)["message"]["content"]

    print(response_text)
    return {"message": response_text}
