CREATE TABLE IF NOT EXISTS variants (
    product_id VARCHAR(64), -- Product ID
    size VARCHAR(32), -- Product Size (XS, S, M, ..., 32, 34, 36, ...)
    color VARCHAR(32), -- Product Color (Blue, Green, Red, ...)
    stock INT, -- Number of Available Units
    internal_id INT, -- Internal Variant ID (rarely for external use)
    FOREIGN KEY (product_id) REFERENCES products(id),
    PRIMARY KEY (product_id, size, color)
);