from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import connection

class BookViewSet(viewsets.ViewSet):
    def list(self, request):
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM books")
            books = cursor.fetchall()
        return Response(books)

    def retrieve(self, request, pk=None):
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM books WHERE id = %s", [pk])
            book = cursor.fetchone()
        if book:
            return Response(book)
        return Response(status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def rate(self, request, pk=None):
        user_id = request.user.id
        rating = request.data.get('rating')
        if not 1 <= rating <= 5:
            return Response({"error": "Rating must be between 1 and 5"}, status=status.HTTP_400_BAD_REQUEST)

        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO ratings (user_id, book_id, rating)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, book_id) DO UPDATE
                SET rating = EXCLUDED.rating
            """, [user_id, pk, rating])
        return Response(status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def filter_by_genre(self, request):
        genre = request.query_params.get('genre')
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM books WHERE genre = %s", [genre])
            books = cursor.fetchall()
        return Response(books)
