CREATE TABLE categories (
    product_id INT,
    category VARCHAR(255),
    FOREIGN KEY (product_id) REFERENCES products(id),
    PRIMARY KEY (product_id, category)
);