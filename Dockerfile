FROM python:3.10-alpine3.14 AS build-image

RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    cargo \
    g++ \
    git \
    && if [[ $(uname -m) == armv6* ||  $(uname -m) == armv7* ]]; then \
          mkdir -p ~/.cargo/registry/index \
          && cd ~/.cargo/registry/index \
          && git clone --bare https://github.com/rust-lang/crates.io-index.git github.com-1285ae84e5963aae; \
        fi
        # workaround for cryptography arm build issue: see https://github.com/pyca/cryptography/issues/6673

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --upgrade pip && pip3 install -r requirements.txt

COPY . .
RUN python3 setup.py install


FROM python:3.10-alpine3.14

COPY --from=build-image /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

RUN apk add --no-cache binutils openssl-dev

RUN mkdir -p /skill/config \
    && mkdir -p /skill/data

ENV JELLYFIN_ALEXA_SKILL_CONFIG=/skill/config/skill.conf
ENV JELLYFIN_ALEXA_SKILL_DATA=/skill/data

ENTRYPOINT ["jellyfin_alexa_skill"]

LABEL org.opencontainers.image.source="https://github.com/infinityofspace/jellyfin_alexa_skill"
LABEL org.opencontainers.image.licenses="GPL-3.0"
