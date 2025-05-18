-- db_seed.sql: 20 mock tables with comments for LLM/semantic indexing

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
COMMENT ON TABLE users IS 'Stores registered user accounts.';
COMMENT ON COLUMN users.id IS 'Primary key for users.';
COMMENT ON COLUMN users.username IS 'Unique username for login.';
COMMENT ON COLUMN users.email IS 'User email address, must be unique.';
COMMENT ON COLUMN users.created_at IS 'Timestamp of registration.';
INSERT INTO users (username, email) VALUES
('alice', 'alice@example.com'),
('bob', 'bob@example.com'),
('carol', 'carol@example.com');

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    price NUMERIC(10,2),
    in_stock BOOLEAN
);
COMMENT ON TABLE products IS 'Catalog of products available for sale.';
COMMENT ON COLUMN products.id IS 'Primary key for products.';
COMMENT ON COLUMN products.name IS 'Product display name.';
COMMENT ON COLUMN products.price IS 'Retail price in USD.';
COMMENT ON COLUMN products.in_stock IS 'True if product is in stock.';
INSERT INTO products (name, price, in_stock) VALUES
('Widget', 19.99, true),
('Gadget', 29.99, false),
('Thingamajig', 9.99, true);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    order_date DATE,
    total NUMERIC(10,2)
);
COMMENT ON TABLE orders IS 'Records of customer purchases.';
COMMENT ON COLUMN orders.id IS 'Primary key for orders.';
COMMENT ON COLUMN orders.user_id IS 'User who placed the order.';
COMMENT ON COLUMN orders.order_date IS 'Date the order was placed.';
COMMENT ON COLUMN orders.total IS 'Total order value in USD.';
INSERT INTO orders (user_id, order_date, total) VALUES
(1, '2025-04-01', 39.98),
(2, '2025-04-02', 9.99);

CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100)
);
COMMENT ON TABLE customers IS 'Business customers.';
COMMENT ON COLUMN customers.id IS 'Primary key for customers.';
COMMENT ON COLUMN customers.name IS 'Customer name.';
COMMENT ON COLUMN customers.email IS 'Contact email.';
INSERT INTO customers (name, email) VALUES
('Dave', 'dave@company.com'),
('Eve', 'eve@company.com');

CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    department_id INTEGER
);
COMMENT ON TABLE employees IS 'Company employees.';
COMMENT ON COLUMN employees.id IS 'Primary key for employees.';
COMMENT ON COLUMN employees.name IS 'Employee full name.';
COMMENT ON COLUMN employees.department_id IS 'Department foreign key.';
INSERT INTO employees (name, department_id) VALUES
('Frank', 1),
('Grace', 2);

CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100)
);
COMMENT ON TABLE departments IS 'Departments in the company.';
COMMENT ON COLUMN departments.id IS 'Primary key for departments.';
COMMENT ON COLUMN departments.name IS 'Department name.';
INSERT INTO departments (name) VALUES
('Engineering'),
('HR');

CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100)
);
COMMENT ON TABLE categories IS 'Product categories.';
COMMENT ON COLUMN categories.id IS 'Primary key for categories.';
COMMENT ON COLUMN categories.name IS 'Category name.';
INSERT INTO categories (name) VALUES
('Electronics'),
('Home');

CREATE TABLE suppliers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100)
);
COMMENT ON TABLE suppliers IS 'Product suppliers.';
COMMENT ON COLUMN suppliers.id IS 'Primary key for suppliers.';
COMMENT ON COLUMN suppliers.name IS 'Supplier company name.';
INSERT INTO suppliers (name) VALUES
('Acme Corp'),
('Globex');

CREATE TABLE inventory (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER
);
COMMENT ON TABLE inventory IS 'Tracks product inventory levels.';
COMMENT ON COLUMN inventory.id IS 'Primary key for inventory.';
COMMENT ON COLUMN inventory.product_id IS 'Product foreign key.';
COMMENT ON COLUMN inventory.quantity IS 'Units in stock.';
INSERT INTO inventory (product_id, quantity) VALUES
(1, 100),
(2, 0);

CREATE TABLE sales (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    sale_date DATE,
    quantity INTEGER
);
COMMENT ON TABLE sales IS 'Records of product sales.';
COMMENT ON COLUMN sales.id IS 'Primary key for sales.';
COMMENT ON COLUMN sales.product_id IS 'Product sold.';
COMMENT ON COLUMN sales.sale_date IS 'Date of sale.';
COMMENT ON COLUMN sales.quantity IS 'Quantity sold.';
INSERT INTO sales (product_id, sale_date, quantity) VALUES
(1, '2025-04-10', 2),
(3, '2025-04-11', 1);

CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    user_id INTEGER REFERENCES users(id),
    rating INTEGER,
    comment TEXT
);
COMMENT ON TABLE reviews IS 'Product reviews by users.';
COMMENT ON COLUMN reviews.id IS 'Primary key for reviews.';
COMMENT ON COLUMN reviews.product_id IS 'Reviewed product.';
COMMENT ON COLUMN reviews.user_id IS 'Reviewer (user) foreign key.';
COMMENT ON COLUMN reviews.rating IS 'Rating out of 5.';
COMMENT ON COLUMN reviews.comment IS 'Review text.';
INSERT INTO reviews (product_id, user_id, rating, comment) VALUES
(1, 1, 5, 'Great!'),
(2, 2, 4, 'Good.');

CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    amount NUMERIC(10,2),
    paid_at TIMESTAMP
);
COMMENT ON TABLE payments IS 'Order payment records.';
COMMENT ON COLUMN payments.id IS 'Primary key for payments.';
COMMENT ON COLUMN payments.order_id IS 'Order foreign key.';
COMMENT ON COLUMN payments.amount IS 'Payment amount in USD.';
COMMENT ON COLUMN payments.paid_at IS 'Timestamp payment was made.';
INSERT INTO payments (order_id, amount, paid_at) VALUES
(1, 39.98, NOW());

CREATE TABLE shipments (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    shipped_at TIMESTAMP
);
COMMENT ON TABLE shipments IS 'Order shipment tracking.';
COMMENT ON COLUMN shipments.id IS 'Primary key for shipments.';
COMMENT ON COLUMN shipments.order_id IS 'Order foreign key.';
COMMENT ON COLUMN shipments.shipped_at IS 'Timestamp shipment sent.';
INSERT INTO shipments (order_id, shipped_at) VALUES
(1, NOW());

CREATE TABLE addresses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    address VARCHAR(200)
);
COMMENT ON TABLE addresses IS 'User address book.';
COMMENT ON COLUMN addresses.id IS 'Primary key for addresses.';
COMMENT ON COLUMN addresses.user_id IS 'User foreign key.';
COMMENT ON COLUMN addresses.address IS 'Street address.';
INSERT INTO addresses (user_id, address) VALUES
(1, '123 Main St'),
(2, '456 Oak Ave');

CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    event_date DATE
);
COMMENT ON TABLE events IS 'Company or product events.';
COMMENT ON COLUMN events.id IS 'Primary key for events.';
COMMENT ON COLUMN events.name IS 'Event name.';
COMMENT ON COLUMN events.event_date IS 'Date of event.';
INSERT INTO events (name, event_date) VALUES
('Launch', '2025-05-01');

CREATE TABLE logs (
    id SERIAL PRIMARY KEY,
    message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
COMMENT ON TABLE logs IS 'System/application logs.';
COMMENT ON COLUMN logs.id IS 'Primary key for logs.';
COMMENT ON COLUMN logs.message IS 'Log message.';
COMMENT ON COLUMN logs.created_at IS 'Timestamp of log entry.';
INSERT INTO logs (message) VALUES
('System started'),
('User login');

CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    sender_id INTEGER,
    receiver_id INTEGER,
    content TEXT
);
COMMENT ON TABLE messages IS 'User-to-user messages.';
COMMENT ON COLUMN messages.id IS 'Primary key for messages.';
COMMENT ON COLUMN messages.sender_id IS 'Sender user id.';
COMMENT ON COLUMN messages.receiver_id IS 'Receiver user id.';
COMMENT ON COLUMN messages.content IS 'Message body.';
INSERT INTO messages (sender_id, receiver_id, content) VALUES
(1, 2, 'Hello!'),
(2, 1, 'Hi!');

CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    message TEXT,
    read BOOLEAN
);
COMMENT ON TABLE notifications IS 'User notifications.';
COMMENT ON COLUMN notifications.id IS 'Primary key for notifications.';
COMMENT ON COLUMN notifications.user_id IS 'User foreign key.';
COMMENT ON COLUMN notifications.message IS 'Notification text.';
COMMENT ON COLUMN notifications.read IS 'True if notification has been read.';
INSERT INTO notifications (user_id, message, read) VALUES
(1, 'Welcome!', false);

CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100),
    completed BOOLEAN
);
COMMENT ON TABLE tasks IS 'Project or personal tasks.';
COMMENT ON COLUMN tasks.id IS 'Primary key for tasks.';
COMMENT ON COLUMN tasks.title IS 'Task title.';
COMMENT ON COLUMN tasks.completed IS 'True if task is completed.';
INSERT INTO tasks (title, completed) VALUES
('Setup', true),
('Test', false);

CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    owner_id INTEGER
);
COMMENT ON TABLE projects IS 'Projects owned by users.';
COMMENT ON COLUMN projects.id IS 'Primary key for projects.';
COMMENT ON COLUMN projects.name IS 'Project name.';
COMMENT ON COLUMN projects.owner_id IS 'Owner user id.';
INSERT INTO projects (name, owner_id) VALUES
('Alpha', 1),
('Beta', 2);
