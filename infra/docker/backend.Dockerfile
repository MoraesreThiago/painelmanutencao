FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app/backend

COPY backend/requirements /tmp/requirements

RUN pip install --upgrade pip \
    && pip install -r /tmp/requirements/prod.txt

COPY backend /app/backend

EXPOSE 8000
