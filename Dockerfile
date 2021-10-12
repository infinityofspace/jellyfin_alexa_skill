FROM python:3.9-slim

WORKDIR /app

RUN mkdir -p /var/lib/jellyfin_alexa_skill/config && mkdir -p /var/lib/jellyfin_alexa_skill/data

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN pip install --no-cache-dir .

ENTRYPOINT ["jellyfin_alexa_skill"]

LABEL org.opencontainers.image.source="https://github.com/infinityofspace/jellyfin_alexa_skill"
LABEL org.opencontainers.image.licenses="GPL-3.0"
