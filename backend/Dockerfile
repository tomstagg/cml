FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies only (layer cached until pyproject.toml/uv.lock change)
COPY pyproject.toml uv.lock ./
RUN uv export --frozen --no-dev -o /tmp/requirements.txt \
    && uv pip install --system --no-cache -r /tmp/requirements.txt

# Install project itself (needs source present)
COPY . .
RUN uv pip install --system --no-cache --no-deps .

RUN chmod +x start.sh

EXPOSE 8000
CMD ["./start.sh"]
