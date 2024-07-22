## use postgres dockerize

docker run --name postgresDB --env POSTGRES_PASSWORD=admin --volume postgres-volume:/var/lib/postgresql/data --publish 5432:5432 --detach postgres
