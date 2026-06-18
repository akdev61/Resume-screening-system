FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# system deps for psycopg2 and building packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# install python deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# copy project
COPY . /app

# uploads dir
RUN mkdir -p /app/uploads

# make entrypoint executable
RUN chmod +x /app/entrypoint.sh || true

ENV DATABASE_URL=postgresql://postgres:postgres@db:5432/resume_screening

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
