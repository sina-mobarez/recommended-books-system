from django.core.management.base import BaseCommand
from django.db import connection
from django.contrib.auth.models import User
import random


class Command(BaseCommand):
    help = "Sets up the database tables and fills them with sample data"

    def handle(self, *args, **kwargs):
        self.stdout.write("Creating tables...")
        self.create_tables()

        self.stdout.write("Creating users...")
        self.create_users()

        self.stdout.write("Filling tables with sample data...")
        self.fill_tables()

        self.stdout.write(self.style.SUCCESS("Database setup completed successfully!"))

    def create_tables(self):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS books (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    author VARCHAR(255) NOT NULL,
                    genre VARCHAR(100) NOT NULL
                )
            """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS ratings (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES auth_user(id),
                    book_id INTEGER REFERENCES books(id),
                    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                    UNIQUE (user_id, book_id)
                )
            """
            )
            cursor.execute(
                """
                CREATE EXTENSION IF NOT EXISTS vector;
            """
            )
            cursor.execute(
                """
                ALTER TABLE books ADD COLUMN IF NOT EXISTS embedding vector(1536);
            """
            )

    def create_users(self):
        for i in range(1, 6):
            username = f"user{i}"
            email = f"user{i}@example.com"
            password = "password123"
            User.objects.create_user(username=username, email=email, password=password)

    def fill_tables(self):
        books_data = [
            ("Book A1", "Author 1", "Adventure"),
            ("Book A2", "Author 1", "Mystery"),
            ("Book A3", "Author 1", "Science Fiction"),
            ("Book B1", "Author 2", "History"),
            ("Book B2", "Author 2", "Romance"),
            ("Book B3", "Author 2", "Science"),
            ("Book C1", "Author 3", "Cooking"),
            ("Book C2", "Author 3", "Gardening"),
            ("Book C3", "Author 3", "Travel"),
            ("Book D1", "Author 4", "Adventure"),
            ("Book D2", "Author 4", "Adventure"),
            ("Book D3", "Author 4", "Adventure"),
            ("Book E1", "Author 5", "Mystery"),
            ("Book E2", "Author 5", "Mystery"),
            ("Book E3", "Author 5", "Mystery"),
            ("Book F1", "Author 6", "Science"),
            ("Book F2", "Author 7", "History"),
            ("Book F3", "Author 8", "Romance"),
            ("Book F4", "Author 9", "Science Fiction"),
            ("Book F5", "Author 10", "Cooking"),
            ("Book F6", "Author 11", "Gardening"),
            ("Book F7", "Author 12", "Travel"),
            ("Book F8", "Author 13", "Education"),
            ("Book F9", "Author 14", "Horror"),
            ("Book F10", "Author 15", "Adventure"),
            ("Book F11", "Author 16", "Mystery"),
            ("Book F12", "Author 17", "Science"),
            ("Book F13", "Author 18", "History"),
            ("Book F14", "Author 19", "Romance"),
            ("Book F15", "Author 20", "Science Fiction"),
            ("Book F16", "Author 21", "Cooking"),
            ("Book F17", "Author 22", "Gardening"),
            ("Book F18", "Author 23", "Travel"),
            ("Book F19", "Author 24", "Education"),
            ("Book F20", "Author 25", "Horror"),
            ("Book F21", "Author 6", "Romance"),
            ("Book F22", "Author 7", "Adventure"),
            ("Book F23", "Author 8", "Mystery"),
            ("Book F24", "Author 9", "Science"),
            ("Book F25", "Author 10", "History"),
            ("Book F26", "Author 11", "Romance"),
            ("Book F27", "Author 12", "Science Fiction"),
            ("Book F28", "Author 13", "Cooking"),
            ("Book F29", "Author 14", "Gardening"),
            ("Book F30", "Author 15", "Travel"),
            ("Book F31", "Author 16", "Education"),
            ("Book F32", "Author 17", "Horror"),
            ("Book F33", "Author 18", "Adventure"),
            ("Book F34", "Author 19", "Mystery"),
            ("Book F35", "Author 20", "Science"),
            ("Book F36", "Author 21", "History"),
            ("Book F37", "Author 22", "Romance"),
            ("Book F38", "Author 23", "Science Fiction"),
            ("Book F39", "Author 24", "Cooking"),
            ("Book F40", "Author 25", "Gardening"),
            ("Book F41", "Author 6", "Travel"),
            ("Book F42", "Author 7", "Education"),
            ("Book F43", "Author 8", "Horror"),
            ("Book F44", "Author 9", "Adventure"),
            ("Book F45", "Author 10", "Mystery"),
            ("Book F46", "Author 11", "Science"),
            ("Book F47", "Author 12", "History"),
            ("Book F48", "Author 13", "Romance"),
            ("Book F49", "Author 14", "Science Fiction"),
            ("Book F50", "Author 15", "Cooking"),
        ]

        with connection.cursor() as cursor:
            for book in books_data:
                cursor.execute(
                    """
                    INSERT INTO books (title, author, genre)
                    VALUES (%s, %s, %s)
                """,
                    book,
                )

            # Generate some random ratings
            users = User.objects.all()
            for user in users:
                for book_id in range(1, len(books_data) + 1):
                    if random.choice([True, False]):  # Randomly decide to rate or not
                        rating = random.randint(1, 5)
                        cursor.execute(
                            """
                            INSERT INTO ratings (user_id, book_id, rating)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (user_id, book_id) DO UPDATE
                            SET rating = EXCLUDED.rating
                        """,
                            [user.id, book_id, rating],
                        )
