\connect catalog_db;

CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    genre VARCHAR(100),
    media_type VARCHAR(50) NOT NULL,
    isbn VARCHAR(20) UNIQUE,
    publication_year INT,
    description TEXT,
    total_copies INT NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_items_title ON items(title);
CREATE INDEX idx_items_author ON items(author);
CREATE INDEX idx_items_genre ON items(genre);
CREATE INDEX idx_items_media_type ON items(media_type);

INSERT INTO items (title, author, genre, media_type, isbn, publication_year, description, total_copies)
VALUES
('The Hobbit', 'J.R.R. Tolkien', 'Fantasy', 'Book', '9780547928227', 1937, 'Classic fantasy novel', 3),
('1984', 'George Orwell', 'Dystopian', 'Book', '9780451524935', 1949, 'Dystopian political fiction', 2),
('Dune', 'Frank Herbert', 'Science Fiction', 'Book', '9780441172719', 1965, 'Epic science fiction novel', 4);
