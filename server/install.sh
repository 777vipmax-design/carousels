#!/usr/bin/env bash
# Установка сервера для каруселей: kie.ai обложки, озвучка ElevenLabs, рилсы.
# Запуск (от root):  bash <(curl -fsSL https://raw.githubusercontent.com/777vipmax-design/carousels/main/server/install.sh)
set -euo pipefail

[ "$(id -u)" = 0 ] || { echo "Запусти от root"; exit 1; }

REPO_URL=https://github.com/777vipmax-design/carousels.git
APP=/opt/carousel
REPO=$APP/repo
FILES=/var/lib/carousel/files
IP=$(ip -4 route get 1.1.1.1 | awk '{for(i=1;i<=NF;i++) if($i=="src") print $(i+1)}')
DOMAIN=${DOMAIN:-$(echo "$IP" | tr . -).sslip.io}

echo "== 1/6 Пакеты (git, ffmpeg, python, caddy)"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq git ffmpeg python3 python3-pil caddy openssl curl >/dev/null

echo "== 2/6 Файл подкачки"
if ! swapon --show | grep -q .; then
  fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile >/dev/null && swapon /swapfile
  grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

echo "== 3/6 Код"
mkdir -p "$APP" "$FILES"
chmod 755 /var/lib/carousel "$FILES"
if [ -d "$REPO/.git" ]; then git -C "$REPO" pull -q --ff-only; else git clone -q --depth 1 "$REPO_URL" "$REPO"; fi

echo "== 4/6 Ключи"
if [ ! -f /etc/carousel.env ]; then
  KIE=""
  while [ -z "$KIE" ]; do
    read -rsp "Вставь ключ kie.ai (символы не видны) и нажми Enter: " KIE </dev/tty; echo
  done
  TOKEN=$(openssl rand -hex 20)
  umask 077
  cat > /etc/carousel.env <<EOF
KIE_API_KEY=$KIE
MCP_TOKEN=$TOKEN
DOMAIN=$DOMAIN
FILES_DIR=$FILES
REPO_DIR=$REPO
PORT=8000
EOF
  umask 022
fi
# shellcheck disable=SC1091
. /etc/carousel.env

echo "== 5/6 Службы"
cat > /etc/systemd/system/carousel-mcp.service <<EOF
[Unit]
Description=Carousel media server
After=network-online.target

[Service]
EnvironmentFile=/etc/carousel.env
WorkingDirectory=$REPO/server
ExecStart=/usr/bin/python3 $REPO/server/app.py
Restart=always
RestartSec=3
UMask=0022

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/caddy/Caddyfile <<EOF
$DOMAIN {
	encode gzip
	handle_path /f/* {
		root * $FILES
		file_server
	}
	handle /mcp/* {
		reverse_proxy 127.0.0.1:8000
	}
	handle /health {
		reverse_proxy 127.0.0.1:8000
	}
	handle {
		respond 404
	}
}
EOF

echo "0 4 * * * root find $FILES -type f -mtime +30 -delete" > /etc/cron.d/carousel-clean
cat > /usr/local/bin/carousel-url <<'EOF'
#!/bin/sh
. /etc/carousel.env && echo "https://$DOMAIN/mcp/$MCP_TOKEN"
EOF
chmod +x /usr/local/bin/carousel-url

if command -v ufw >/dev/null && ufw status | grep -q "Status: active"; then
  ufw allow 80/tcp >/dev/null; ufw allow 443/tcp >/dev/null
fi

systemctl daemon-reload
systemctl enable -q --now carousel-mcp
systemctl restart carousel-mcp
systemctl enable -q caddy
systemctl restart caddy

echo "== 6/6 Проверка https (до минуты)"
OK=0
for i in $(seq 1 20); do
  if curl -fsS "https://$DOMAIN/health" >/dev/null 2>&1; then OK=1; break; fi
  sleep 3
done
echo
if [ $OK = 1 ]; then echo "ГОТОВО, https работает."; else echo "https пока не ответил — пришли скриншот, разберёмся."; fi
echo
echo "АДРЕС ДЛЯ КОННЕКТОРА (скопируй целиком):"
echo
echo "https://$DOMAIN/mcp/$MCP_TOKEN"
echo
echo "Показать адрес ещё раз: carousel-url"
