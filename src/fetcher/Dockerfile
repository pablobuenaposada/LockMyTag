FROM python:3.13-slim

WORKDIR /app

COPY apple /app/apple
COPY main.py pyproject.toml uv.lock /app/

RUN apt-get update && apt-get install -y git
ENV UV_PROJECT_ENVIRONMENT="/usr/local/"
RUN pip install --no-cache-dir uv
RUN uv sync
CMD ["python", "main.py"]