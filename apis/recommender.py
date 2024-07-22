from django.db import connection


def get_recommendations(user_id, method):
    # First, check if the user has rated any books
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*) FROM ratings WHERE user_id = %s
        """,
            [user_id],
        )
        rating_count = cursor.fetchone()[0]

    if rating_count == 0:
        return {
            "message": "There is not enough data about you to make recommendations."
        }

    if method == "genre":
        return recommend_by_genre(user_id)
    elif method == "author":
        return recommend_by_author(user_id)
    elif method == "similar_users":
        return recommend_by_similar_users(user_id)
    else:
        raise ValueError("Invalid recommendation method")


def recommend_by_genre(user_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT b.* FROM books b
            JOIN ratings r ON b.id = r.book_id
            WHERE b.genre IN (
                SELECT DISTINCT b2.genre
                FROM books b2
                JOIN ratings r2 ON b2.id = r2.book_id
                WHERE r2.user_id = %s
            )
            AND b.id NOT IN (
                SELECT book_id FROM ratings WHERE user_id = %s
            )
            GROUP BY b.id
            ORDER BY AVG(r.rating) DESC
            LIMIT 10
        """,
            [user_id, user_id],
        )
        recommendations = cursor.fetchall()

    if not recommendations:
        return {"message": "No recommendations found based on your genre preferences."}
    return recommendations


def recommend_by_author(user_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT b.* FROM books b
            WHERE b.author IN (
                SELECT DISTINCT b2.author
                FROM books b2
                JOIN ratings r2 ON b2.id = r2.book_id
                WHERE r2.user_id = %s
            )
            AND b.id NOT IN (
                SELECT book_id FROM ratings WHERE user_id = %s
            )
            LIMIT 10
        """,
            [user_id, user_id],
        )
        recommendations = cursor.fetchall()

    if not recommendations:
        return {"message": "No recommendations found based on your author preferences."}
    return recommendations


def recommend_by_similar_users(user_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT b.* FROM books b
            JOIN ratings r ON b.id = r.book_id
            WHERE r.user_id IN (
                SELECT DISTINCT r2.user_id
                FROM ratings r2
                WHERE r2.book_id IN (
                    SELECT book_id FROM ratings WHERE user_id = %s
                )
                AND r2.user_id != %s
            )
            AND b.id NOT IN (
                SELECT book_id FROM ratings WHERE user_id = %s
            )
            GROUP BY b.id
            ORDER BY AVG(r.rating) DESC
            LIMIT 10
        """,
            [user_id, user_id, user_id],
        )
        recommendations = cursor.fetchall()

    if not recommendations:
        return {
            "message": "No recommendations found based on similar users' preferences."
        }
    return recommendations
