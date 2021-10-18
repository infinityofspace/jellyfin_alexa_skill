FROM python:3.9-slim AS build-image

RUN apt update && apt install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    cargo

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --upgrade pip wheel && pip3 install -r requirements.txt

COPY . .
RUN pip3 install .


FROM python:3.9-slim

COPY --from=build-image /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

RUN useradd -ms /bin/bash skill

RUN mkdir -p /skill/config \
    && mkdir -p /skill/data \
    && chown -R skill:skill /skill

USER skill

ENV JELLYFIN_ALEXA_SKILL_CONFIG=/skill/config/skill.conf
ENV JELLYFIN_ALEXA_SKILL_DATA=/skill/data

ENTRYPOINT ["jellyfin_alexa_skill"]

LABEL org.opencontainers.image.source="https://github.com/infinityofspace/jellyfin_alexa_skill"
LABEL org.opencontainers.image.licenses="GPL-3.0"
