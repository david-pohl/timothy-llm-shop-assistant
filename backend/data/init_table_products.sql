CREATE TABLE IF NOT EXISTS products (
    id INT PRIMARY KEY, -- Unique Product ID
    name VARCHAR(255), -- Name
    text TEXT, -- Description
    bullets TEXT, -- Enumeration of special product attributes
    price DECIMAL(10, 2), -- Price ($)
    stock INT, -- Number of available units
    img VARCHAR(255), -- Link to the product image
    sku VARCHAR(255), -- Stock-Keeping Unit of the specific product (rarely of external use)
    parent VARCHAR(255) -- Stock-Keeping Unit of the product type (rarely of external use)
);