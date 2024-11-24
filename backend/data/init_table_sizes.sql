CREATE TABLE sizes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT,
    size VARCHAR(50),
    FOREIGN KEY (product_id) REFERENCES products(id)
);