FROM python:3.13-slim

WORKDIR /app

COPY api /app/api
COPY locations /app/locations
COPY account /app/account
COPY locks /app/locks
COPY notifications /app/notifications
COPY main /app/main
COPY tests /app/tests
COPY .python-version manage.py pyproject.toml uv.lock /app/

RUN pip install --no-cache-dir uv
ENV UV_PROJECT_ENVIRONMENT="/usr/local/"
RUN uv sync