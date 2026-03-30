\connect circulation_db;

CREATE TABLE item_state (
    item_id INT PRIMARY KEY,
    state VARCHAR(50) NOT NULL CHECK (state IN ('AVAILABLE', 'RESERVED', 'CHECKED_OUT', 'OVERDUE')),
    checked_out_by INT,
    reserved_by INT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE loans (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    item_id INT NOT NULL,
    borrowed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    due_date TIMESTAMP NOT NULL,
    returned_at TIMESTAMP,
    status VARCHAR(50) NOT NULL CHECK (status IN ('ACTIVE', 'RETURNED', 'OVERDUE'))
);

CREATE TABLE reservations (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    item_id INT NOT NULL,
    reserved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    queue_position INT,
    status VARCHAR(50) NOT NULL CHECK (status IN ('ACTIVE', 'FULFILLED', 'CANCELLED'))
);

CREATE INDEX idx_item_state_state ON item_state(state);
CREATE INDEX idx_loans_user_id ON loans(user_id);
CREATE INDEX idx_loans_item_id ON loans(item_id);
CREATE INDEX idx_loans_status ON loans(status);
CREATE INDEX idx_reservations_user_id ON reservations(user_id);
CREATE INDEX idx_reservations_item_id ON reservations(item_id);
CREATE INDEX idx_reservations_status ON reservations(status);

CREATE UNIQUE INDEX unique_active_item_loan
ON loans (item_id)
WHERE status = 'ACTIVE';

INSERT INTO item_state (item_id, state, checked_out_by, reserved_by)
VALUES
(1, 'AVAILABLE', NULL, NULL),
(2, 'CHECKED_OUT', 1, NULL),
(3, 'RESERVED', NULL, 2);

INSERT INTO loans (user_id, item_id, due_date, status)
VALUES
(1, 2, CURRENT_TIMESTAMP + INTERVAL '14 days', 'ACTIVE');

INSERT INTO reservations (user_id, item_id, queue_position, status)
VALUES
(2, 3, 1, 'ACTIVE');