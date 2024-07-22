import openai
from celery import shared_task
from django.conf import settings
from django.db import connection

openai.api_key = settings.OPENAI_API_KEY


@shared_task
def vectorize_book(book_id):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT title, author, genre FROM books WHERE id = %s", [book_id]
        )
        book = cursor.fetchone()

    if not book:
        return

    title, author, genre = book
    text = f"{title} {author} {genre}"

    response = openai.Embedding.create(input=text, model="text-embedding-ada-002")
    embedding = response["data"][0]["embedding"]

    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE books
            SET embedding = %s
            WHERE id = %s
        """,
            [embedding, book_id],
        )


@shared_task
def vectorize_all_books():
    with connection.cursor() as cursor:
        cursor.execute("SELECT id FROM books")
        book_ids = [row[0] for row in cursor.fetchall()]

    for book_id in book_ids:
        vectorize_book.delay(book_id)
