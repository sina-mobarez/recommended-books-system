## use postgres dockerize

docker run --name postgresDB --env POSTGRES_PASSWORD=admin --env POSTGRES_DB=postgres --env POSTGRES_USER=postgres --env POSTGRES_HOST_AUTH_METHOD=trust --publish 5432:5432 --detach ankane/pgvector

for run celery :
docker run -d -p 5672:5672 rabbitmq
celery -A core worker --loglevel=info
