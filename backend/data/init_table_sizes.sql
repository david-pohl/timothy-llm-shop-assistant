CREATE TABLE IF NOT EXISTS sizes (
    id INT AUTO_INCREMENT PRIMARY KEY, -- Database ID (not for external use)
    product_id INT, -- Unique Product ID
    size VARCHAR(50), -- Available size
    FOREIGN KEY (product_id) REFERENCES products(id)
);