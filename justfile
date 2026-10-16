default:
    @just --list --unsorted

# --- run on this machine, against a database in docker ---

[group('local')]
makemigrations:
    docker compose -f docker-compose.yml -f docker-compose.tests.yml --env-file .env.local up -d --force-recreate db
    POSTGRES_HOST=localhost PYTHONPATH=src uv --directory src/backoffice run --env-file ../../.env.local manage.py makemigrations

[group('local')]
test:
    docker compose -f docker-compose.yml -f docker-compose.tests.yml --env-file .env.local up -d --force-recreate db
    POSTGRES_HOST=localhost POSTGRES_DB=lockmytag_test PYTHONPATH=src uv --directory src/backoffice run --env-file ../../.env.local --group tests pytest tests -s

[group('local')]
format:
    uv --directory src/backoffice run --group tests ruff format
    uv --directory src/backoffice run --group tests ruff check --fix
    uv --directory src/fetcher run --group tests ruff format
    uv --directory src/fetcher run --group tests ruff check --fix
    npx dclint . -r --fix
    cd src/frontend && npx prettier --write "**/*.{html,css}"
    cd src/frontend && npx eslint . --fix

[group('local')]
format-check:
    uv --directory src/backoffice run --group tests ruff format --check
    uv --directory src/backoffice run --group tests ruff check
    uv --directory src/fetcher run --group tests ruff format --check
    uv --directory src/fetcher run --group tests ruff check
    npx dclint . -r
    cd src/frontend && npx prettier --check "**/*.{html,css}"
    cd src/frontend && npx eslint .

# --- run inside the containers ---

[group('docker')]
up:
    docker compose --env-file .env.local up -d --force-recreate --build

[group('docker')]
up-prod:
    docker compose --env-file .env.prod up -d --force-recreate --build

[group('docker')]
test-docker:
    docker compose --env-file .env.local up -d --force-recreate db backoffice
    docker exec lockmytag-backoffice-1 uv run --group tests pytest tests

[group('docker')]
migrations-check:
    docker compose --env-file .env.local up -d --force-recreate db backoffice
    docker exec lockmytag-backoffice-1 uv run python manage.py makemigrations --check --dry-run

[group('docker')]
create-super-user:
    docker exec lockmytag-backoffice-1 env DJANGO_SUPERUSER_PASSWORD=admin uv run python manage.py createsuperuser --username admin --email foo@bar.com --noinput

[group('docker')]
db-shell:
    docker exec -it lockmytag-db-1 psql -U $(grep POSTGRES_USER .env.local | cut -d= -f2-) -d $(grep POSTGRES_DB .env.local | cut -d= -f2-)

[group('docker')]
db-dump:
    #!/usr/bin/env bash
    # The shebang has to be the first line: it makes the whole recipe run in
    # one shell, so the prompts and the command using them are not separate
    read -p "Enter database user: " db_user
    read -sp "Enter database password: " db_pass; echo
    docker exec -e PGPASSWORD="$db_pass" lockmytag-db-1 pg_dump -U "$db_user" -d "lockmytag" -Fc > db_dump.lockmytag
    echo "✓ Database dumped to db_dump.lockmytag"

[group('docker')]
db-load:
    #!/usr/bin/env bash
    read -p "Enter database user: " db_user
    read -sp "Enter database password: " db_pass; echo
    docker exec -i -e PGPASSWORD="$db_pass" lockmytag-db-1 pg_restore -U "$db_user" -d "lockmytag" --clean --if-exists --no-owner --no-privileges < db_dump.lockmytag
    echo "✓ Database restored from db_dump.lockmytag"
