-- 1. SEED USERS
INSERT INTO users (username, password_hash, email, user_role) VALUES
    ('admin_sarah', 'ef92b778', 'sarah@foodbank.org', 'admin'),
    ('volunteer_tim', '5e884898', 'tim.jones@school.edu', 'volunteer'),
    ('citizen_jane', '86f7e437', 'jane.doe@gmail.com', 'citizen'),
    ('mmichael', 'fnaf1983', 'matthewsmichaelg@scps.net', 'citizen'),
    ('cdarya', 'something', 'cherrydarya@scps.net', 'citizen'),
    ('csamman', 'qwerty', 'sammancaseyk@scps.net', 'citizen');

-- 2. SEED LIBRARY
INSERT INTO library (title, author, lexile, genre) VALUES 
    ('49 Miles Alone', 'Natlalie D. Richards', 620, 'suspense'), 
    ('The Code Breaker', 'Walter Isaacson', 1180, 'science'),
    ('A Good Girls Guide to Murder', 'Holly Jackson', 700, 'suspense'),
    ('The Dysfunctional Family''s Guide to Murder', 'Kate Emery', NULL, 'Young Adult'),
    ('The Love Hypothesis', 'Ali Hazelwood', 620, 'Romance'),
    ('Cinder', 'Marissa Meyer', 700, 'Fantasy'),
    ('The Diary of a Young Girl', 'Anne Frank', 720, 'Nonfiction'),
    ('Diary of a Wimpy Kid', 'Jeff Kinney', 500, 'Realistic Fiction'),
    ('Artemis Fowl', 'Eoin Colfer', 540, 'Science Fiction'),
    ('Six of Crows', 'Leigh Bardugo', 720, 'Fantasy'),
    ('The Long Walk', 'Stephen King', 700, 'Dystopian'),
    ('JoJo''s Bizarre Adventure: Battle Tendency Vol 1', 'Hirohiko Araki', 600, 'Manga'), 
    ('Welcome to the Ballroom Heat 2', 'Tomo Takeuchi', NULL, 'Sports'),
    ('A Beautiful and Terrible Murder', 'Claire Andrews', NULL, 'Mystery'),
    ('The Hunger Games', 'Suzanne Collins', 810, 'Dystopian'),
    ('Percy Jackson & the Olympians: The Lightning Thief', 'Rick Riordan', 680, 'Fantasy'),
    ('Harry Potter and the Sorcerer''s Stone', 'J.K. Rowling', 880, 'Fantasy'),
    ('The Book Thief', 'Markus Zusak', 730, 'Historical Fiction'),
    ('To Kill a Mockingbird', 'Harper Lee', 870, 'Classic Fiction'),
    ('Fahrenheit 451', 'Ray Bradbury', 890, 'Dystopian'),
    ('The Giver', 'Lois Lowry', 760, 'Dystopian'),
    ('The Fault in Our Stars', 'John Green', 850, 'Realistic Fiction'),
    ('Divergent', 'Veronica Roth', 700, 'Dystopian'),
    ('One of Us Is Lying', 'Karen M. McManus', 730, 'Mystery'),
    ('Legend', 'Marie Lu', 710, 'Dystopian'),
    ('Holes', 'Louis Sachar', 660, 'Adventure'),
    ('The Maze Runner', 'James Dashner', 770, 'Sci-Fi');

-- 3. SEED COMMUNITY RESOURCES
INSERT INTO community_resources (resource_name, category, description, quantity_available, managed_by_user_id) VALUES
    ('Downtown Literacy Hub', 'Facility', 'Quiet reading space with public computers', 1, 1),
    ('Children''s Book Pack', 'Materials', 'Set of 10 beginner reading books', 5, 2),
    ('Study Desk Set', 'Furniture', 'Single desk and chair for home study', 3, 2);

-- 4. SEED REQUESTS
INSERT INTO requests (user_id, request_title, request_author, request_genre, quantity_requested, status) VALUES
    (3, 'Fahrenheit 451', 'Ray Bradbury', 'Dystopian', 1, 'pending'),
    (4, 'To Kill a Mockingbird', 'Harper Lee', 'Classic Fiction', 1, 'approved'),
    (1, '1984', 'George Orwell', 'Dystopian', 2, 'pending');

-- 5. SEED DONATIONS
INSERT INTO donations (user_id, resource_id, quantity_donated, notes) VALUES
    (3, 2, 2, 'Donated lightly used children books for the hub'),
    (4, 3, 1, 'Donated desk in good condition');