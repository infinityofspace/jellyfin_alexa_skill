FROM python:3.9-slim AS build-image

RUN apt-get update && apt-get install -y \
    gcc \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY requirements.txt .
RUN pip3 install wheel && pip3 install -r requirements.txt

COPY . .
RUN pip3 install .


FROM python:3.9-slim

RUN mkdir -p /var/lib/jellyfin_alexa_skill/config && mkdir -p /var/lib/jellyfin_alexa_skill/data

COPY --from=build-image /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

RUN useradd -ms /bin/bash skill
USER skill

ENTRYPOINT ["jellyfin_alexa_skill"]

LABEL org.opencontainers.image.source="https://github.com/infinityofspace/jellyfin_alexa_skill"
LABEL org.opencontainers.image.licenses="GPL-3.0"
