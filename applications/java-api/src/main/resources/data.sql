INSERT INTO books (title, author, year) VALUES
    ('Pride and Prejudice', 'Jane Austen', 1813),
    ('Moby-Dick', 'Herman Melville', 1851),
    ('Crime and Punishment', 'Fyodor Dostoevsky', 1866),
    ('The Adventures of Sherlock Holmes', 'Arthur Conan Doyle', 1892),
    ('The Time Machine', 'H. G. Wells', 1895)
ON CONFLICT (title) DO NOTHING;
