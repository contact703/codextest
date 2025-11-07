#!/usr/bin/env bash
set -euo pipefail

VIDEO_URL="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
OUTPUT_VIDEO="$(dirname "$0")/domain_public.mp4"

if command -v yt-dlp >/dev/null 2>&1; then
  yt-dlp "$VIDEO_URL" -o "$OUTPUT_VIDEO"
else
  curl -L "$VIDEO_URL" -o "$OUTPUT_VIDEO"
fi

echo "Vídeo salvo em $OUTPUT_VIDEO"
