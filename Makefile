local/makemigrations:
	PYTHONPATH=src uv --directory src/api run --env-file .env.tests manage.py makemigrations

local/tests:
	docker compose up -d --force-recreate db
	PYTHONPATH=src uv --directory src/api run --env-file .env.tests --group tests pytest tests -s