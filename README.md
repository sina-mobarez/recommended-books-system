# Recommended Books System

Restful apis for a system that show user a list of books and recommended books by user rating, and similar books (in this project tried to use raw sql instead ORM)

## Installation

in this project we use Postgresql (vector support) for database, and celery for async operations and run tasks in Rabbitmq.
sure you installed them in local machine or use dockerize images.

for run postgresql in docker:

```bash
docker run --name postgresDB --env POSTGRES_PASSWORD=admin --env POSTGRES_DB=postgres --env POSTGRES_USER=postgres --env POSTGRES_HOST_AUTH_METHOD=trust --publish 5432:5432 --detach ankane/pgvector
```

for run rabbitmq (celery use it, also you can use redis):

```bash
docker run -d -p 5672:5672 rabbitmq
```

## Run Locally

Clone the project

```bash
  git clone https://github.com/sina-mobarez/recommended-books-system.git
```

Go to the project directory

```bash
  cd recommended-books-system
```

Install dependencies

```bash
  pip install requirements.txt
```

migrate and fill database

```bash
  python manage.py migrate
  python manage.py setup_db
```

Start the Celery

```bash
  celery -A core worker --loglevel=info
```

Vectoring all books in db

```bash
  python manage.py vectorize_books
```

Start the Server

```bash
  python manage.py runserver
```

- make sure active a virtual environment before install dependencies.

## Demo

![pipeline_recording](demo.gif)

## Tech Stack

**Server:** Python, Django, RestFramework. Swagger. Celery, Clip, Torch

## Contributing

Contributions are always welcome!
You can ask me about this project by email

## License

[MIT](https://choosealicense.com/licenses/mit/)
