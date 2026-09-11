FROM python:3.12-slim

WORKDIR /app

COPY apps/api/pyproject.toml /app/pyproject.toml
COPY apps/api/src /app/src
COPY apps/api/migrations /app/migrations
COPY apps/api/alembic.ini /app/alembic.ini
RUN pip install --no-cache-dir -e .

ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "infrastructure.start_server"]
