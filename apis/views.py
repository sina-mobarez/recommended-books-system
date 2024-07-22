from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import viewsets, views, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import connection
from apis.recommender import get_recommendations
from django.contrib.auth import authenticate
from django.conf import settings
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
import jwt
from datetime import datetime, timedelta
import openai


openai.api_key = settings.OPENAI_API_KEY

book_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "id": openapi.Schema(type=openapi.TYPE_INTEGER),
        "title": openapi.Schema(type=openapi.TYPE_STRING),
        "author": openapi.Schema(type=openapi.TYPE_STRING),
        "genre": openapi.Schema(type=openapi.TYPE_STRING),
    },
)


recommendation_response = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "recommendations": openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=book_schema,
        ),
        "message": openapi.Schema(type=openapi.TYPE_STRING),
    },
)


class BookViewSet(viewsets.ViewSet):
    @swagger_auto_schema(
        operation_description="List all books with the current user's ratings",
        responses={
            200: openapi.Response(
                description="Success",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                            "title": openapi.Schema(type=openapi.TYPE_STRING),
                            "author": openapi.Schema(type=openapi.TYPE_STRING),
                            "genre": openapi.Schema(type=openapi.TYPE_STRING),
                            "user_rating": openapi.Schema(
                                type=openapi.TYPE_INTEGER, nullable=True
                            ),
                        },
                    ),
                ),
            )
        },
    )
    def list(self, request):
        user_id = request.user.id
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT b.id, b.title, b.author, b.genre, r.rating as user_rating
                FROM books b
                LEFT JOIN ratings r ON b.id = r.book_id AND r.user_id = %s
                ORDER BY b.id
            """,
                [user_id],
            )
            columns = [col[0] for col in cursor.description]
            books = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return Response(books)

    @swagger_auto_schema(
        operation_description="Retrieve a specific book",
        responses={200: "Success", 404: "Not found"},
    )
    def retrieve(self, request, pk=None):
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM books WHERE id = %s", [pk])
            book = cursor.fetchone()
        if book:
            return Response(book)
        return Response(status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        method="post",
        operation_description="Rate a book or update an existing rating",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "rating": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="Rating between 1 and 5"
                )
            },
            required=["rating"],
        ),
        responses={201: "Created", 200: "Updated", 400: "Bad Request"},
    )
    @swagger_auto_schema(
        method="delete",
        operation_description="Delete a rating for a book",
        responses={204: "No Content", 404: "Not Found"},
    )
    @action(detail=True, methods=["post", "delete"])
    def rate(self, request, pk=None):
        user_id = request.user.id

        if request.method == "POST":
            rating = request.data.get("rating")
            if not rating or not 1 <= rating <= 5:
                return Response(
                    {"error": "Rating must be between 1 and 5"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO ratings (user_id, book_id, rating)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id, book_id) DO UPDATE
                    SET rating = EXCLUDED.rating
                    RETURNING (xmax = 0) AS created
                    """,
                    [user_id, pk, rating],
                )
                created = cursor.fetchone()[0]

            if created:
                return Response(
                    {"message": "Rating created"}, status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    {"message": "Rating updated"}, status=status.HTTP_200_OK
                )

        elif request.method == "DELETE":
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM ratings
                    WHERE user_id = %s AND book_id = %s
                    RETURNING id
                    """,
                    [user_id, pk],
                )
                deleted = cursor.fetchone()

            if deleted:
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(
                    {"error": "Rating not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

    @swagger_auto_schema(
        operation_description="Filter books by genre",
        manual_parameters=[
            openapi.Parameter(
                "genre",
                openapi.IN_QUERY,
                description="Genre to filter by",
                type=openapi.TYPE_STRING,
            )
        ],
        responses={200: "Success"},
    )
    @action(detail=False, methods=["get"])
    def filter_by_genre(self, request):
        genre = request.query_params.get("genre")
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM books WHERE genre = %s", [genre])
            books = cursor.fetchall()
        return Response(books)

    @swagger_auto_schema(
        operation_description="Get book recommendations based on user's ratings",
        responses={
            200: openapi.Response(
                description="Successful response",
                schema=recommendation_response,
                examples={
                    "application/json": {
                        "recommendations": [
                            {
                                "id": 1,
                                "title": "To Kill a Mockingbird",
                                "author": "Harper Lee",
                                "genre": "Fiction",
                            },
                            {
                                "id": 2,
                                "title": "1984",
                                "author": "George Orwell",
                                "genre": "Science Fiction",
                            },
                        ]
                    }
                },
            ),
            400: "Bad Request: Invalid recommendation method",
            401: "Unauthorized: User not authenticated",
        },
        operation_summary="Get book recommendations",
    )
    @action(detail=False, methods=["get"])
    def recommendations(self, request):
        user_id = request.user.id
        method = settings.RECOMMENDATION_METHOD
        recommendations = get_recommendations(user_id, method)

        if isinstance(recommendations, dict) and "message" in recommendations:
            return Response(recommendations, status=status.HTTP_200_OK)

        return Response(recommendations, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Get 10 books similar to the specified book",
        responses={
            200: openapi.Response(
                description="Successful response",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                            "title": openapi.Schema(type=openapi.TYPE_STRING),
                            "author": openapi.Schema(type=openapi.TYPE_STRING),
                            "genre": openapi.Schema(type=openapi.TYPE_STRING),
                            "similarity": openapi.Schema(type=openapi.TYPE_NUMBER),
                        },
                    ),
                ),
            ),
            404: "Book not found",
        },
    )
    @action(detail=True, methods=["get"])
    def similar_books(self, request, pk=None):
        # Get the book details
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT title, author, genre, embedding
                FROM books
                WHERE id = %s
            """,
                [pk],
            )
            book = cursor.fetchone()

        if not book:
            return Response(
                {"error": "Book not found"}, status=status.HTTP_404_NOT_FOUND
            )

        title, author, genre, embedding = book

        # Find similar books
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, title, author, genre,
                       1 - (embedding <=> %s) AS similarity
                FROM books
                WHERE id != %s
                ORDER BY similarity DESC
                LIMIT 10
            """,
                [embedding, pk],
            )
            similar_books = cursor.fetchall()

        # Format the recommendations
        formatted_recommendations = [
            {
                "id": book[0],
                "title": book[1],
                "author": book[2],
                "genre": book[3],
                "similarity": book[4],
            }
            for book in similar_books
        ]

        return Response(formatted_recommendations)


class RegisterView(views.APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "username": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Username"
                ),
                "email": openapi.Schema(type=openapi.TYPE_STRING, description="Email"),
                "password": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Password"
                ),
            },
        ),
        responses={201: "Created", 400: "Bad Request"},
    )
    def post(self, request):
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")

        if not username or not email or not password:
            return Response(
                {"error": "Please provide username, email and password"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {"error": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.create_user(
            username=username, email=email, password=password
        )
        return Response(
            {"message": "User created successfully"}, status=status.HTTP_201_CREATED
        )


class LoginView(views.APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "username": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Username"
                ),
                "password": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Password"
                ),
            },
        ),
        responses={200: "Success", 401: "Unauthorized"},
    )
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)

        if user is not None:
            payload = {"user_id": user.id, "exp": datetime.utcnow() + timedelta(days=1)}
            token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
            return Response({"token": token})
        else:
            return Response(
                {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )
