local/makemigrations:
	PYTHONPATH=src uv --directory src/api run --env-file .env.tests manage.py makemigrations

local/tests:
	docker compose up -d --force-recreate db
	PYTHONPATH=src uv --directory src/api run --env-file .env.tests --group tests pytest tests -s

local/format:
	uv --directory src/api run --group tests ruff format
	uv --directory src/api run --group tests ruff check --fix
	uv --directory src/fetcher run --group tests ruff format
	uv --directory src/fetcher run --group tests ruff check --fix
	npx dclint . -r --fix

docker/migrations-check:
	docker compose up -d --force-recreate db django
	docker exec lockmytag-django-1 uv run python manage.py makemigrations --check --dry-run

docker/tests:
	docker compose up -d --force-recreate db django
	docker exec lockmytag-django-1 uv run --group tests pytest tests

docker/create-super-user:
	docker exec lockmytag-django-1 uv run python manage.py createsuperuser --noinput

docker/up:
	docker compose up -d --force-recreate --build