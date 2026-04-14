FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /tmp/web-requirements.txt
RUN pip install --no-cache-dir -r /tmp/web-requirements.txt

COPY . /app

EXPOSE 3000 3001

CMD ["sh", "-c", "reflex run --env prod --backend-host 0.0.0.0"]
