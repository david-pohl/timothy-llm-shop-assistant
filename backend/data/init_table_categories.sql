CREATE TABLE IF NOT EXISTS categories (
    product_id VARCHAR(64), -- Product ID
    category VARCHAR(255), -- Assigned Category
    FOREIGN KEY (product_id) REFERENCES products(id),
    PRIMARY KEY (product_id, category)
);