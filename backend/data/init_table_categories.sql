CREATE TABLE IF NOT EXISTS categories (
    product_id INT, -- Unique Product ID
    category VARCHAR(255), -- Assigned category
    FOREIGN KEY (product_id) REFERENCES products(id),
    PRIMARY KEY (product_id, category)
);