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

LLAMA_MODEL = "llama3.2:1b"

# System prompt passed to the llm for general guidance when generating SQL queries
SYSTEM_MESSAGE_SQL = {"role": "system", "content": """\
You are Timothy, an AI assistant specialized in generating SQL queries for an online clothing retail inventory system.
Given user requests, return only the SQL query that satisfies their query. 
If the user request is not a valid question or cannot be addressed with an SQL query, respond with 'None'. 
Do not include any explanations, comments, or additional details in your responses.\
"""}

# System prompt passed to the llm for general guidance when generating the final response based on the SQL queries and results
SYSTEM_MESSAGE_RESPONSE = {"role": "system", "content": """\
You are Timothy, an AI assistant of an online clothing retail inventory system. 
Respond to the user based on their request, the corresponding SQL query and result. 
Answer concisely based only on the given information and previous conversation. 
Never include technical aspects. Do not mention SQL.\
"""}

# Prompt passed to the llm wrapping the user question for accurate SQL query generation
# Knowledge of the existing tables is passed using the initialization .sql scripts
# Using one-shot + chain-of-thought prompting
GET_PROMPT_SQL = lambda question: f"""\
Given a user question, create a syntactically correct SQL query. Only if the question builds on prior messages, use corresponding messages as context.
Unless the question specifies a specific number of items to obtain, query for at most 5 results using the LIMIT clause as per MySQL. 
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

# Prompt passed to the llm wrapping user question, SQL query (may be none), and SQL result (may be none)
# Inspired by langchain's internal prompt
GET_PROMPT_RESPONSE = lambda question, query, result: f"""\
Given the following user question, corresponding SQL query, and SQL result, respond concisely to the user. 
If there is no SQL query or result, politely ask for further clarification. 

Question: {question};
SQL Query: {query};
SQL Result: {result};
Answer: \
"""

# Initial data based on scrape from fixed date
TIME_INIT_DATA = ["2024", "11", "27", "00", "30", "04"]
app.last_data_update = TIME_INIT_DATA

# Retrieving a new connector to the product database
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DATABASE_HOST"),
        user=os.getenv("DATABASE_USER"),
        password=os.getenv("DATABASE_PASSWORD"),
        database=os.getenv("DATABASE_NAME")
    )

# Initializing the database with pre-scraped data (saved as .json on the server) for a quick start into using the app
def init_db(products):
    prod_cols = ["id", "name", "price", "description", "features"]
    prod_sql = f"""INSERT IGNORE INTO products ({", ".join(prod_cols)}) VALUES ({", ".join(["%s"] * len(prod_cols))})"""
    
    cat_cols = ["product_id", "category"]
    cat_sql = f"""INSERT IGNORE INTO categories ({", ".join(cat_cols)}) VALUES ({", ".join(["%s"] * len(cat_cols))})"""

    variants_cols = ["product_id", "size", "color", "stock", "internal_id"]
    variants_sql = f"""INSERT IGNORE INTO variants ({", ".join(variants_cols)}) VALUES ({", ".join(["%s"] * len(variants_cols))})"""
    
    prod_vals, cat_vals, variants_vals = [], [], []
    for product_id, details in tqdm(products.items(), desc="Populating Database"):
        # Skipping products without a price
        if details["price"] is None:
            continue

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


# Initializing database on server start
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


class APIMessage(BaseModel):
    role: str
    content: str

class APIRequest(BaseModel):
    messages: List[APIMessage]


# Sending query to database
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

# Sending prompt to internal llm using ollama (currently tiny llms used)
def prompt_internal(messages):
    ollama_url = os.getenv("OLLAMA_CHAT_URL")
    response_text = ""
    for chunk in post(
        url=ollama_url, 
        json={
            "model": LLAMA_MODEL,
            "messages": messages
        }).text.splitlines():
        print(json.loads(chunk))
        response_text += json.loads(chunk)["message"]["content"]

    return response_text

# Sending prompt to external cohere api
def prompt_external(messages):
    cohere_api_key = os.getenv("COHERE_API_KEY")
    co = cohere.ClientV2(cohere_api_key)
    response = co.chat(
        model="command-r",
        messages=messages
    )
    return response.message.content[0].text


def process(messages, use_external_llm):
    user_query = messages[-1]["content"]
    print(user_query)

    messages[-1]["content"] = GET_PROMPT_SQL(messages[-1]["content"])

    if not use_external_llm:
        sql_query = prompt_internal([SYSTEM_MESSAGE_SQL] + messages)
    else:
        sql_query = prompt_external([SYSTEM_MESSAGE_SQL] + messages)

    print(sql_query)

    if sql_query.startswith("SELECT"):
        sql_result = execute_query(sql_query)
        if sql_result != "error":
            sql_result = sql_result[:5]
    else:
        sql_result = "error"

    print(sql_result)

    messages[-1]["content"] = GET_PROMPT_RESPONSE(user_query, sql_query, sql_result)

    if not use_external_llm:
        final_response = prompt_internal([SYSTEM_MESSAGE_RESPONSE] + messages)
    else:
        final_response = prompt_external([SYSTEM_MESSAGE_RESPONSE] + messages)

    print(final_response)

    return {"response": final_response}


# Processing user message: question -> sql query -> sql result -> response
@app.post("/send/message")
async def send_message(user_request: UserRequest):
    messages = [
        {
            "role": "assistant" if m.sender == "Timothy" else "user",
            "content": m.text
        } 
        for m in user_request.messages
    ]
    return process(messages, user_request.use_external_llm)


@app.post("/chat/completions")
async def chat_completions(api_request: APIRequest):
    messages = [
        {
            "role": m.role,
            "content": m.content
        } 
        for m in api_request.messages
    ]

    return process(messages, True)


# Providing client with connection status of backend: checking database and llm connections
@app.get("/is-ready")
async def is_ready():
    try:
        # Checking database connection
        with get_db_connection() as conn:
            if not conn.is_connected():
                raise Exception()
        
        print("DB Connection Successful")

        # Checking internal llm connection
        """ollama_list_url = os.getenv("OLLAMA_LIST_URL")
        response = get(ollama_list_url)

        print(response)

        model_found = False
        for model in response["models"]:
            print(model)
            if model["name"] == LLAMA_MODEL:
                model_found = True
        
        if not model_found:
            raise Exception()

        print("OLLAMA Connection Successful")"""

        # Checking external llm connection
        co = cohere.ClientV2(COHERE_API_KEY)
        print("COHERE Connection Successful")

        return {"version": app.last_data_update[:3]}
    except:
        raise HTTPException(status_code=500, detail=f"Backend Connection To Other Services Failed")


# Updating data through new scrape
@app.get("/update-data")
async def update_data():
    try:
        products, filename_date = scrape(True)
        init_db(products)
        app.last_data_update = filename_date.split("_")[:3]
        return {"version": app.last_data_update}
    except:
        return HTTPException(status_code=500, detail="Updating Data Failed")
