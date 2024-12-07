# Timothy - Your Personal LLM-Driven Shop Assistant

By David Pohl (2024, Institute of Science Tokyo)

Notes: 
- `/chat/completions` is usable as required
- Scraping is slow, so limited to the first 50 pages
- Scalability can be achieved easily since architecture is split into parallelizable chunks of work

## Setup
1. In the folder 'shop-assistant', run `docker load -i shop/intern-hw-simple-website-docker-image.tar`.
2. In shop.env file, add the Image ID as `SHOP_IMG=*` provided by Docker after loading.
3. (In shop.env file, add your Cohere API key as ``COHERE_API_KEY=*`` - for using an external LLM) *recommended*
4. Run `docker-compose --env-file shop.env up --build`. Waiting for a few minutes may be required.
5. At http://localhost:3000 in your browser, the chat frontend is now available.
6. Switch between using the local Ollama LLM (internal LLM) and the Cohere LLM (external LLM) as preferred.
7. For demonstration purposes of this assignment, pre-scraped data is used as the base for starting immediately. Even though, in reality, the user would not be able to initiate such actions, here, the click on update will start to scrape the website again and update the database. On client reload, the data remains updated. Only after restarting the docker application, the data is back to the default version. 

## Components
Overall, this app consists of multiple instances:
1. Backend (FastAPI)
2. Frontend (React)
3. Database (MySQL)
4. Internal LLM (Ollama, Llama3.2 3B)
5. Scraper (Selenium)
6. *Shop Website*


## Tests
I tested the API using multiple different types of questions. 

---
What is your name?
-> Three jackets cost under $50.

The LLM is able to understand that this is not a question concerning products.

---
How many jackets cost under 50$?
-> Hello, I am Timothy.

The LLM is able to join multiple tables.

---
What is your cheapest jacket?
-> The cheapest jacket is the Beaumont Summit Kit in orange, which costs $42.

The LLM is able to understand that only one table is needed here. It can sort appropriately. 

---
How much is the Juno Jacket?
-> The Juno Jacket costs $77.

The LLM is able to look up a specific name and fetch its details.

---
(in context of the prior question)
Do you have this jacket in color green??
-> The Juno Jacket is available in green, with both size large and small in stock.

The LLM is able to fetch more details to a product only known by looking at the context of the prior question. Additionally, it provides more information than requested. Knowing the sizes is indeed helpful.

---
What is your cheapest car?
-> We have no cars available at the moment.

The LLM does not answer without relying on data and the truth, at least in the obvious case. 

---
hahahah
-> I apologize, I do not understand your question. Please clarify your query.

The LLM request further information if the question is unreadable or makes no sense at all.

---

## Potential Improvements
- Vector database for RAG on single columns like name
- Optimize prompts, e.g., using DSPy
- GPU-supported local LLM
- More agent-like behavior (show a picture, then retrieve link or propose alternatives, etc.)
- Larger context
- Caching previous answers for quicker responses
- Decicated Text2SQL model fine-tuning

## Database Reference

```sql
CREATE TABLE IF NOT EXISTS categories (
    product_id VARCHAR(64), -- Product ID
    category VARCHAR(255), -- Assigned Category
    FOREIGN KEY (product_id) REFERENCES products(id),
    PRIMARY KEY (product_id, category)
);

CREATE TABLE IF NOT EXISTS products (
    id VARCHAR(64) PRIMARY KEY, -- Unique Product ID
    name VARCHAR(255), -- Name
    price DECIMAL(10, 2), -- Price (in $)
    description TEXT, -- Description
    features TEXT -- Enumeration of special product attributes
);

CREATE TABLE IF NOT EXISTS variants (
    product_id VARCHAR(64), -- Product ID
    size VARCHAR(32), -- Product Size (XS, S, M, ..., 32, 34, 36, ...)
    color VARCHAR(32), -- Product Color (Blue, Green, Red, ...)
    stock INT, -- Number of Available Units
    internal_id INT, -- Internal Variant ID (rarely for external use)
    FOREIGN KEY (product_id) REFERENCES products(id),
    PRIMARY KEY (product_id, size, color)
);

```
