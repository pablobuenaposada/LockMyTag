local/makemigrations:
	PYTHONPATH=src uv --directory src/api run --env-file .env.tests manage.py makemigrations

local/tests:
	docker compose up -d --force-recreate db
	PYTHONPATH=src uv --directory src/api run --env-file .env.tests --group tests pytest tests -s

local/format:
	uv --directory src/api run ruff format
	uv --directory src/api run ruff check --fix

docker/migrations-check:
	docker compose up -d --force-recreate db django
	docker exec lockmytag-django-1 uv run python manage.py makemigrations --check --dry-run

docker/tests:
	docker compose up -d --force-recreate db django
	docker exec lockmytag-django-1 uv run --group tests pytest tests