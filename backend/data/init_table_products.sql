CREATE TABLE products (
    id INT PRIMARY KEY,
    name VARCHAR(255),
    sku VARCHAR(255),
    parent VARCHAR(255),
    price DECIMAL(10, 2),
    stock INT,
    img VARCHAR(255),
    text TEXT,
    bullets TEXT
);