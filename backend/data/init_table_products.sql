CREATE TABLE IF NOT EXISTS products (
    id VARCHAR(64) PRIMARY KEY, -- Unique Product ID
    name VARCHAR(255), -- Name
    price DECIMAL(10, 2), -- Price (in $)
    description TEXT, -- Description
    features TEXT -- Enumeration of special product attributes
);