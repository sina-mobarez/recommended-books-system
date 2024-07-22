import torch
import clip
from celery import shared_task
from django.db import connection

device = "cuda" if torch.cuda.is_available() else "cpu"


@shared_task
def vectorize_book(book_id):
    # Load the CLIP model and preprocess function within the task
    model, preprocess = clip.load("ViT-B/32", device=device)

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT title, author, genre FROM books WHERE id = %s", [book_id]
        )
        book = cursor.fetchone()

    if not book:
        return

    title, author, genre = book
    text = f"{title} {author} {genre}"

    # Preprocess the text and get the embedding
    text_input = clip.tokenize([text]).to(device)
    with torch.no_grad():
        embedding = model.encode_text(text_input).cpu().numpy().tolist()[0]

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
