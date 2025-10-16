local/makemigrations:
	docker compose -f docker-compose.yml -f docker-compose.tests.yml --env-file .env.local up -d --force-recreate db
	POSTGRES_HOST=localhost PYTHONPATH=src uv --directory src/backoffice run --env-file ../../.env.local manage.py makemigrations

local/tests:
	docker compose -f docker-compose.yml -f docker-compose.tests.yml --env-file .env.local up -d --force-recreate db
	POSTGRES_HOST=localhost POSTGRES_DB=lockmytag_test PYTHONPATH=src uv --directory src/backoffice run --env-file ../../.env.local --group tests pytest tests -s

local/format:
	uv --directory src/backoffice run --group tests ruff format
	uv --directory src/backoffice run --group tests ruff check --fix
	uv --directory src/fetcher run --group tests ruff format
	uv --directory src/fetcher run --group tests ruff check --fix
	npx dclint . -r --fix
	cd src/frontend && npx eslint --fix
	cd src/frontend && npx stylelint "**/*.css" --fix

docker/migrations-check:
	docker compose --env-file .env.local up -d --force-recreate db backoffice
	docker exec lockmytag-backoffice-1 uv run python manage.py makemigrations --check --dry-run

docker/tests:
	docker compose --env-file .env.local up -d --force-recreate db backoffice
	docker exec lockmytag-backoffice-1 uv run --group tests pytest tests

docker/create-super-user:
	docker exec lockmytag-backoffice-1 env DJANGO_SUPERUSER_PASSWORD=admin uv run python manage.py createsuperuser --username admin --email foo@bar.com --noinput

docker/up:
	docker compose --env-file .env.local up -d --force-recreate --build

docker/up-prod:
	docker compose --env-file .env.prod up -d --force-recreate --build