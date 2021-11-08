FROM python:3.10-alpine3.14 AS build-image

RUN apk add --no-cache \
    gcc \
    musl-dev \
    python3-dev \
    libffi-dev \
    openssl-dev \
    cargo \
    g++

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY requirements-docker-build.txt .
RUN pip3 install --upgrade pip && pip3 install -r requirements-docker-build.txt

COPY . .
RUN pip3 install .


FROM python:3.10-alpine3.14

COPY --from=build-image /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

RUN apk add --no-cache binutils openssl-dev

RUN addgroup -S skill && adduser -S skill -G skill

RUN mkdir -p /skill/config \
    && mkdir -p /skill/data \
    && chown -R skill:skill /skill

USER skill

ENV JELLYFIN_ALEXA_SKILL_CONFIG=/skill/config/skill.conf
ENV JELLYFIN_ALEXA_SKILL_DATA=/skill/data

ENTRYPOINT ["jellyfin_alexa_skill"]

LABEL org.opencontainers.image.source="https://github.com/infinityofspace/jellyfin_alexa_skill"
LABEL org.opencontainers.image.licenses="GPL-3.0"
