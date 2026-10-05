#!/usr/bin/env bash
# Добавить ключ ElevenLabs на сервер:  bash /opt/carousel/repo/server/setkey.sh
set -euo pipefail
git -C /opt/carousel/repo pull -q --ff-only || true
read -rsp "Вставь API-ключ ElevenLabs (символы не видны) и нажми Enter: " KEY </dev/tty; echo
[ -n "$KEY" ] || { echo "Пусто, ничего не меняю"; exit 1; }
sed -i '/^ELEVENLABS_API_KEY=/d' /etc/carousel.env
echo "ELEVENLABS_API_KEY=$KEY" >> /etc/carousel.env
systemctl restart carousel-mcp
echo "Готово: ключ ElevenLabs сохранён, сервер перезапущен."
