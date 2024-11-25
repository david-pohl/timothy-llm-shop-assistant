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

with open("backend/data/init_table_products.sql", "r") as f:
    SQL_INIT_TABLE_PRODUCTS = f.read()
with open("backend/data/init_table_sizes.sql", "r") as f:
    SQL_INIT_TABLE_SIZES = f.read()
with open("backend/data/init_table_categories.sql", "r") as f:
    SQL_INIT_TABLE_CATEGORIES = f.read()

PROMPT_SYSTEM = """\
You are Timothy, an AI assistant specialized in generating SQL queries for an online clothing retail inventory system.
Given user requests, return only the SQL query that satisfies their query. 
If the user request is not a valid question or cannot be addressed with an SQL query, respond with 'None'. 
Do not include any explanations, comments, or additional details in your responses.\
"""

GET_PROMPT_USER = lambda question: f"""\
Given a user question, create a syntactically correct SQL query. Only if the question builds on prior messages, use corresponding messages as context.
Unless the question specifies a specific number of items to obtain, query for at most 5 results using the LIMIT clause as per MySQL. 
You can order the results to return the most informative data in the database.
If the question specifies or indicates a set of attributes to retrieve, query only the columns that are needed to answer the question.
Use only the column names you can see in the corresponding tables below. Be careful to not query for columns that do not exist.

Tables:
{SQL_INIT_TABLE_PRODUCTS}
{SQL_INIT_TABLE_SIZES}
{SQL_INIT_TABLE_CATEGORIES}

---
Use the following path to finding a solution as a reference. 
Example Question: "How many jackets cost under $50?":
1. Identify the relevant tables: 'products' for price info; 'categories' as 'jackets' describe a category.
2. Join the tables on the product id. 
3. Filter for products priced under $50. 
4. Match only categories containing the word 'jacket'. 
5. Count the matching rows.

Example SQL query:
SELECT COUNT(*) FROM products AS T1, categories AS T2 WHERE T1.id = T2.product_id AND T1.price < 50 AND T2.category LIKE '%jacket%';
---
Question: 
{question}\
"""

GET_PROMPT_INTERNAL = lambda question, query, result: f"""\
Given the following user question, corresponding SQL query, and SQL result, answer the user question. 
If there is no SQL result, politely suggest that you can assist with finding items in the inventory if applicable. 
If the request does not lend itself to such assistance or is unreadable, respond with 'None'. 

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
    prod_sql = f"""INSERT IGNORE INTO products ({", ".join(prod_cols)}) VALUES ({", ".join(["%s"] * len(prod_cols))})"""
    
    size_cols = ["product_id", "size"]
    size_sql = f"""INSERT IGNORE INTO sizes ({", ".join(size_cols)}) VALUES ({", ".join(["%s"] * len(size_cols))})"""
    
    cat_cols = ["product_id", "category"]
    cat_sql = f"""INSERT IGNORE INTO categories ({", ".join(cat_cols)}) VALUES ({", ".join(["%s"] * len(cat_cols))})"""
    
    with open("backend/data/scraped_2024_11_24_13_17_36.json", "r") as f:
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
        cursor.execute(SQL_INIT_TABLE_PRODUCTS)
        cursor.execute(SQL_INIT_TABLE_SIZES)
        cursor.execute(SQL_INIT_TABLE_CATEGORIES)
        
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
    try:
        connection = get_db_connection()
        if connection.is_connected():
            connection.close()
            return {"status": "ok"}
        else:
            return {"status": "error"}
    except:
        return {"status": "error"}


def execute_query(query):
    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute(query)
        results = cursor.fetchall()

    return results

def execute_prompt(chat_messages):
    system_message = {
        "role": "system",
        "content": PROMPT_SYSTEM
    }

    response_text = ""
    for chunk in post(
        url="http://localhost:11434/api/chat", 
        json={
            "model": "llama3.2:3b",
            "messages": [system_message] + chat_messages
        }).text.splitlines():
        response_text += json.loads(chunk)["message"]["content"]

    return response_text


@app.post("/send/message")
async def send_message(messages: List[Message]):
    user_query = messages[-1].text
    print(user_query)

    chat_messages = [
        {
            "role": "assistant" if m.sender == "Timothy" else "user",
            "content": m.text
        } 
        for m in messages
    ]
    chat_messages[-1]["content"] = GET_PROMPT_USER(chat_messages[-1]["content"])

    sql_query = execute_prompt(chat_messages)
    print(sql_query)

    if sql_query.startswith("SELECT"):
        sql_result = execute_query(sql_query)[:5]
    else:
        sql_result = ""

    print(sql_result)

    chat_messages[-1]["content"] = GET_PROMPT_INTERNAL(user_query, sql_query, sql_result)

    final_response = execute_prompt(chat_messages)
    print(final_response)

    return {"message": final_response}
