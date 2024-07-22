from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import viewsets, views, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import connection
from apis.recommender import get_recommendations
from django.conf import settings
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.conf import settings
import jwt
from datetime import datetime, timedelta


class BookViewSet(viewsets.ViewSet):
    @swagger_auto_schema(
        operation_description="List all books", responses={200: "Success"}
    )
    def list(self, request):
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM books")
            books = cursor.fetchall()
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
        operation_description="Rate a book",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "rating": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="Rating between 1 and 5"
                )
            },
        ),
        responses={201: "Created", 400: "Bad Request"},
    )
    @action(detail=True, methods=["post"])
    def rate(self, request, pk=None):
        user_id = request.user.id
        rating = request.data.get("rating")
        if not 1 <= rating <= 5:
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
            """,
                [user_id, pk, rating],
            )
        return Response(status=status.HTTP_201_CREATED)

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
        operation_description="Get book recommendations", responses={200: "Success"}
    )
    @action(detail=False, methods=["get"])
    def recommendations(self, request):
        user_id = request.user.id
        method = settings.RECOMMENDATION_METHOD
        recommendations = get_recommendations(user_id, method)
        return Response(recommendations)


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
