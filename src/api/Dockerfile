FROM python:3.13

WORKDIR /app

COPY locations /app/locations
COPY main /app/main
COPY tests /app/tests
COPY .python-version manage.py pyproject.toml uv.lock /app/
RUN pip install uv
ENV UV_PROJECT_ENVIRONMENT="/usr/local/"
RUN uv sync