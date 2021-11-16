#!/usr/bin/env bash

./jellyfin/jellyfin \
  --datadir /jellyfin_config \
  --cachedir /cache \
  --ffmpeg /usr/lib/jellyfin-ffmpeg/ffmpeg
