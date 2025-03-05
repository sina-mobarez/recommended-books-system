from django.core.management.base import BaseCommand
from django.db import connection
from django.contrib.auth.models import User
import random
from faker import Faker

class Command(BaseCommand):
    help = "Sets up the database tables and fills them with sample data"

    def __init__(self):
        super().__init__()
        self.fake = Faker()
        self.genres = [
            'Adventure', 'Mystery', 'Science Fiction', 'History', 
            'Romance', 'Science', 'Cooking', 'Gardening', 'Travel', 
            'Education', 'Horror'
        ]

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
            username = self.fake.user_name()
            email = self.fake.email()
            password = "password123"
            User.objects.create_user(username=username, email=email, password=password)

    def fill_tables(self):
        books_data = []

        for _ in range(50):
            books_data.append((
                self.fake.catch_phrase(),
                self.fake.name(),
                random.choice(self.genres)
            ))
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
