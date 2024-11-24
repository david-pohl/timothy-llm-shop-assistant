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

CREATE TABLE sizes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT,
    size VARCHAR(50),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE sizes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT,
    size VARCHAR(50),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255)
);

CREATE TABLE product_categories (
    product_id INT,
    category_id INT,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (category_id) REFERENCES categories(id),
    PRIMARY KEY (product_id, category_id)
);