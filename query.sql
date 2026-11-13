.mode box
.header on

-- 1. Create Table
CREATE TABLE IF NOT EXISTS legacy_users (
    user_id INT PRIMARY KEY,
    username VARCHAR(100),
    email VARCHAR(255),
    password_hash VARCHAR(255),
    user_role VARCHAR(50),
    category VARCHAR(50),
    quantity_available INT
);

-- Clear previous data if needed
DELETE FROM legacy_users;

-- 2. Insert Sample Data with requested names
INSERT INTO legacy_users (user_id, username, email, password_hash, user_role, category, quantity_available)
VALUES 
    (1, 'london', 'london@gmail.com', 'hash_123', 'admin', 'email', 9500),
    (2, 'dc', 'dc@yahoo.com', 'hash_456', 'volunteer', 'support', 4000),
    (3, 'justin', 'justin@gmail.com', 'hash_789', 'user', 'email', 12000),
    (4, 'yaw', 'yaw@gmail.com', 'hash_012', 'volunteer', 'email', 9200);

-- 3. Print Complete Table
SELECT * FROM legacy_users;

-- 4. Query: Category = 'email' AND quantity_available > 9000
SELECT * FROM legacy_users 
WHERE category = 'email' 
  AND quantity_available > 9000;

-- 5. Query: Role is admin OR volunteer
SELECT * FROM legacy_users 
WHERE user_role = 'admin' 
   OR user_role = 'volunteer';

-- 6. Query: Gmail users
SELECT username, email FROM legacy_users 
WHERE email LIKE '%@gmail.com';

-- 7. Query: Ordered by quantity available (Highest first)
SELECT username, email, quantity_available FROM legacy_users 
ORDER BY quantity_available DESC;