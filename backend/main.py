import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import mysql.connector

# debug
import time
import random

from requests import post, get
import json
from typing import List

from tqdm import tqdm
import cohere
from private_vars import COHERE_API_KEY
from scraper import scrape


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Replace with your frontend's origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

with open("data/init_table_products.sql", "r") as f:
    SQL_INIT_TABLE_PRODUCTS = f.read()
with open("data/init_table_categories.sql", "r") as f:
    SQL_INIT_TABLE_CATEGORIES = f.read()
with open("data/init_table_variants.sql", "r") as f:
    SQL_INIT_TABLE_VARIANTS = f.read()

SYSTEM_MESSAGE_SQL = {"role": "system", "content": """\
You are Timothy, an AI assistant specialized in generating SQL queries for an online clothing retail inventory system.
Given user requests, return only the SQL query that satisfies their query. 
If the user request is not a valid question or cannot be addressed with an SQL query, respond with 'None'. 
Do not include any explanations, comments, or additional details in your responses.\
"""}

SYSTEM_MESSAGE_RESPONSE = {"role": "system", "content": """\
You are Timothy, an AI assistant of an online clothing retail inventory system. 
Respond to the user based on their request, a corresponding SQL query, and SQL result. 
Answer precisely based on the given information and previous conversation. Always respond politely and truthfully. 
Never provide an answer while disregarding the given information.\
"""}

GET_PROMPT_SQL = lambda question: f"""\
Given a user question, create a syntactically correct SQL query. Only if the question builds on prior messages, use corresponding messages as context.
Unless the question specifies a specific number of items to obtain, query for at most 5 results using the LIMIT clause as per MySQL. 
You can order the results to return the most informative data in the database.
If the question specifies or indicates a set of attributes to retrieve, query only the columns that are needed to answer the question.
Use only the column names you can see in the corresponding tables below. Be careful to not query for columns that do not exist.

Tables:
{SQL_INIT_TABLE_PRODUCTS}
{SQL_INIT_TABLE_CATEGORIES}
{SQL_INIT_TABLE_VARIANTS}

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

GET_PROMPT_RESPONSE = lambda question, query, result: f"""\
Given the following user question, corresponding SQL query, and SQL result, answer the user question. 
If there is no SQL result, politely suggest that you can assist with finding items in the inventory if applicable. 
If the request cannot be answered properly, ask for clarification politely. 

Question: {question};
SQL Query: {query};
SQL Result: {result};
Answer: \
"""

TIME_INIT_DATA = ["2024", "11", "27", "00", "30", "04"]
app.last_data_update = TIME_INIT_DATA

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DATABASE_HOST"),
        user=os.getenv("DATABASE_USER"),
        password=os.getenv("DATABASE_PASSWORD"),
        database=os.getenv("DATABASE_NAME")
    )

def init_db(products):
    prod_cols = ["id", "name", "price", "description", "features"]
    prod_sql = f"""INSERT IGNORE INTO products ({", ".join(prod_cols)}) VALUES ({", ".join(["%s"] * len(prod_cols))})"""
    
    cat_cols = ["product_id", "category"]
    cat_sql = f"""INSERT IGNORE INTO categories ({", ".join(cat_cols)}) VALUES ({", ".join(["%s"] * len(cat_cols))})"""

    variants_cols = ["product_id", "size", "color", "stock", "internal_id"]
    variants_sql = f"""INSERT IGNORE INTO variants ({", ".join(variants_cols)}) VALUES ({", ".join(["%s"] * len(variants_cols))})"""
    
    prod_vals, cat_vals, variants_vals = [], [], []
    for product_id, details in tqdm(products.items()):
        prod_vals.append(tuple([details[col] if col != "id" else product_id for col in prod_cols]))

        cats = set()
        for category in details["categories"]:
            for level in category:
                if level not in cats:
                    cat_vals.append((product_id, level))
                    cats.add(level)
        
        for internal_id, size, color, stock in details["variants"]:
            variants_vals.append((product_id, size, color, stock, internal_id))

    connection = get_db_connection()

    with connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS categories;")
        cursor.execute("DROP TABLE IF EXISTS variants;")
        cursor.execute("DROP TABLE IF EXISTS products;")
        cursor.execute(SQL_INIT_TABLE_PRODUCTS)
        cursor.execute(SQL_INIT_TABLE_CATEGORIES)
        cursor.execute(SQL_INIT_TABLE_VARIANTS)
        
        connection.commit()

    with connection.cursor() as cursor:
        cursor.executemany(prod_sql, prod_vals)
        cursor.executemany(cat_sql, cat_vals)
        cursor.executemany(variants_sql, variants_vals)  

        connection.commit()

    connection.close()


filename_date_suffix = "_".join(app.last_data_update)
with open(f"data/products_{filename_date_suffix}.json", "r") as f:
    products = json.load(f)
    init_db(products)


class Message(BaseModel):
    sender: str
    text: str

class UserRequest(BaseModel):
    messages: List[Message]
    use_external_llm: bool



def execute_query(query):
    try:
        connection = get_db_connection()
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute(query)
            results = cursor.fetchall()

        return results
    except:
        print("SQL Execution Error")
        return "error"

def prompt_internal(messages):
    ollama_url = os.getenv("OLLAMA_CHAT_URL")
    response_text = ""
    for chunk in post(
        url=ollama_url, 
        json={
            "model": "llama3.2:3b",
            "messages": messages
        }).text.splitlines():
        print(json.loads(chunk))
        response_text += json.loads(chunk)["message"]["content"]

    return response_text

def prompt_external(messages):
    cohere_api_key = os.getenv("COHERE_API_KEY")
    co = cohere.ClientV2(cohere_api_key)
    response = co.chat(
        model="command-r",
        messages=messages
    )
    return response.message.content[0].text


@app.post("/send/message")
async def send_message(user_request: UserRequest):
    user_query = user_request.messages[-1].text
    print(user_query)

    chat_messages = [
        {
            "role": "assistant" if m.sender == "Timothy" else "user",
            "content": m.text
        } 
        for m in user_request.messages
    ]
    chat_messages[-1]["content"] = GET_PROMPT_SQL(chat_messages[-1]["content"])

    if not user_request.use_external_llm:
        sql_query = prompt_internal([SYSTEM_MESSAGE_SQL] + chat_messages)
    else:
        sql_query = prompt_external([SYSTEM_MESSAGE_SQL] + chat_messages)

    print(sql_query)

    if sql_query.startswith("SELECT"):
        sql_result = execute_query(sql_query)
        if sql_result != "error":
            sql_result = sql_result[:5]
    else:
        sql_result = "error"

    print(sql_result)

    chat_messages[-1]["content"] = GET_PROMPT_RESPONSE(user_query, sql_query, sql_result)

    if not user_request.use_external_llm:
        final_response = prompt_internal([SYSTEM_MESSAGE_RESPONSE] + chat_messages)
    else:
        final_response = prompt_external([SYSTEM_MESSAGE_RESPONSE] + chat_messages)

    print(final_response)

    return {"response": final_response}


@app.get("/is-ready")
async def is_ready():
    try:
        # Checking database connection
        with get_db_connection() as conn:
            if not conn.is_connected():
                raise Exception()
        
        llama_model_name = "llama3.2:3b"

        # Checking internal llm connection
        """ollama_list_url = os.getenv("OLLAMA_LIST_URL")
        models = get(ollama_list_url)

        model_found = False
        for model in models:
            print(model)
            if model["name"] == llama_model_name:
                model_found = True
        
        if not model_found:
            raise Exception()"""

        # Checking external llm connection
        co = cohere.ClientV2(COHERE_API_KEY)

        return {"version": app.last_data_update[:3]}
    except:
        raise HTTPException(status_code=500, detail=f"Backend Connection To Other Services Failed")


@app.get("/update-data")
async def update_data():
    try:
        products, filename_date = scrape(True)
        print("products", products)
        init_db(products)
        app.last_data_update = filename_date.split("_")[:3]
        return {"version": app.last_data_update}
    except:
        return HTTPException(status_code=500, detail="Updating Data Failed")
