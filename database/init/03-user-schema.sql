\connect user_db;

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    account_status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
    max_loans INT NOT NULL DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);

INSERT INTO users (full_name, email, account_status, max_loans)
VALUES
('Alice Johnson', 'alice@example.com', 'ACTIVE', 5),
('Bob Smith', 'bob@example.com', 'ACTIVE', 3),
('Charlie Brown', 'charlie@example.com', 'SUSPENDED', 0);
