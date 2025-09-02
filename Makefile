local/makemigrations:
	docker compose -f docker-compose.yml -f docker-compose.tests.yml --env-file .env.local up -d --force-recreate db
	POSTGRES_HOST=localhost PYTHONPATH=src uv --directory src/api run --env-file ../../.env.local manage.py makemigrations

local/tests:
	docker compose -f docker-compose.yml -f docker-compose.tests.yml --env-file .env.local up -d --force-recreate db
	POSTGRES_HOST=localhost POSTGRES_DB=lockmytag_test PYTHONPATH=src uv --directory src/api run --env-file ../../.env.local --group tests pytest tests -s

local/format:
	uv --directory src/api run --group tests ruff format
	uv --directory src/api run --group tests ruff check --fix
	uv --directory src/fetcher run --group tests ruff format
	uv --directory src/fetcher run --group tests ruff check --fix
	npx dclint . -r --fix

docker/migrations-check:
	docker compose --env-file .env.local up -d --force-recreate db django
	docker exec lockmytag-django-1 uv run python manage.py makemigrations --check --dry-run

docker/tests:
	docker compose --env-file .env.local up -d --force-recreate db django
	docker exec lockmytag-django-1 uv run --group tests pytest tests

docker/create-super-user:
	docker exec lockmytag-django-1 uv run python manage.py createsuperuser --noinput

docker/up:
	docker compose --env-file .env.local up -d --force-recreate --build