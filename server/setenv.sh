#!/usr/bin/env bash
# Сохранить ключ на сервере:  bash /opt/carousel/repo/server/setenv.sh PIXABAY_KEY
set -euo pipefail
NAME=${1:?укажи имя переменной, например PIXABAY_KEY}
git -C /opt/carousel/repo pull -q --ff-only || true
read -rsp "Вставь значение $NAME (символы не видны) и нажми Enter: " VAL </dev/tty; echo
[ -n "$VAL" ] || { echo "Пусто, ничего не меняю"; exit 1; }
sed -i "/^$NAME=/d" /etc/carousel.env
echo "$NAME=$VAL" >> /etc/carousel.env
systemctl restart carousel-mcp
echo "Готово: $NAME сохранён, сервер перезапущен."
