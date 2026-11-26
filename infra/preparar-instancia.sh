#!/usr/bin/env bash
# Prepara una instancia Ubuntu 24.04 para CEDIS Flow. Sirve para una instancia dedicada o para una
# compartida con otros proyectos: no toca sus servicios, contenedores ni puertos.
# Se corre una vez, con un usuario que tenga sudo, y se puede repetir sin romper nada:
#
#   curl -fsSL https://raw.githubusercontent.com/ximezh/hackaitver-reto1/dev/infra/preparar-instancia.sh | bash
#
# Qué hace:
#   1. Instala Podman, Caddy y docker-compose (proveedor de `podman compose`) si faltan.
#   2. Crea el usuario `cedis`, que corre los contenedores sin root y sin Docker.
#   3. Clona el repositorio en /home/cedis/reto1.
#   4. Crea los archivos de entorno con secretos aleatorios, si no existen (nunca salen de la instancia).
#   5. Agrega infra/caddy/cedis.caddy al Caddy del sistema: respaldo, validación y recarga sin cortes.
#   6. Instala los timers de despliegue continuo (infra/systemd/) sin activarlos, salvo ACTIVAR=1.
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/ximezh/hackaitver-reto1.git}"
RAMA_SCRIPTS="${RAMA_SCRIPTS:-dev}"
USUARIO=cedis
COMPOSE_VERSION=v2.39.4
CADDYFILE=/etc/caddy/Caddyfile

paso() { echo "==> $*"; }
como_cedis() { sudo -iu "$USUARIO" env XDG_RUNTIME_DIR="/run/user/$(id -u "$USUARIO")" bash -c "$1"; }

paso "Paquetes"
faltan=()
for p in podman uidmap slirp4netns passt git curl caddy; do dpkg -s "$p" >/dev/null 2>&1 || faltan+=("$p"); done
if ((${#faltan[@]})); then
  sudo apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "${faltan[@]}"
fi
if [[ ! -x /usr/local/bin/docker-compose ]]; then
  sudo curl -fsSL -o /usr/local/bin/docker-compose \
    "https://github.com/docker/compose/releases/download/$COMPOSE_VERSION/docker-compose-linux-x86_64"
  sudo chmod +x /usr/local/bin/docker-compose
fi

paso "Usuario $USUARIO"
id "$USUARIO" >/dev/null 2>&1 || sudo useradd --create-home --shell /bin/bash "$USUARIO"
sudo loginctl enable-linger "$USUARIO"
for _ in $(seq 1 20); do [[ -d "/run/user/$(id -u "$USUARIO")" ]] && break; sleep 1; done
como_cedis 'systemctl --user enable --now podman.socket podman-restart.service'
# shellcheck disable=SC2016  # $(id -u) se expande en la sesión de cedis
grep -q DOCKER_HOST "/home/$USUARIO/.profile" 2>/dev/null ||
  echo 'export DOCKER_HOST="unix:///run/user/$(id -u)/podman/podman.sock"' |
  sudo tee -a "/home/$USUARIO/.profile" >/dev/null

paso "Repositorio"
como_cedis "[[ -d ~/reto1/.git ]] || git clone -q -b $RAMA_SCRIPTS $REPO_URL ~/reto1; git -C ~/reto1 pull -q --ff-only"

paso "Archivos de entorno"
# shellcheck disable=SC2016  # las variables se expanden en la sesión de cedis
como_cedis '
set -euo pipefail
cd ~/reto1/infra/entornos
for e in produccion staging; do
  [[ -f $e.env ]] && { echo "  $e.env ya existe"; continue; }
  clave=$(openssl rand -hex 24)
  jwt=$(openssl rand -base64 48 | tr -d "\n/+=" | cut -c1-64)
  sed -e "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$clave|" \
      -e "s|^JWT_SECRET=.*|JWT_SECRET=$jwt|" \
      -e "s|<contraseña-larga>|$clave|" $e.env.example > $e.env
  chmod 600 $e.env
  echo "  $e.env creado con secretos aleatorios"
done'

paso "Caddy del sistema"
sudo cp "/home/$USUARIO/reto1/infra/caddy/cedis.caddy" /etc/caddy/cedis.caddy
if ! sudo grep -q '^import /etc/caddy/cedis.caddy' "$CADDYFILE"; then
  respaldo="$CADDYFILE.bak-cedis-$(date +%Y%m%d-%H%M%S)"
  sudo cp "$CADDYFILE" "$respaldo"
  printf '\n# CEDIS Flow (infra/caddy/cedis.caddy)\nimport /etc/caddy/cedis.caddy\n' | sudo tee -a "$CADDYFILE" >/dev/null
  if ! sudo caddy validate --config "$CADDYFILE" --adapter caddyfile >/dev/null 2>&1; then
    sudo cp "$respaldo" "$CADDYFILE"
    echo "La configuración de Caddy no es válida; se restauró $respaldo" >&2
    exit 1
  fi
  echo "  respaldo en $respaldo"
fi
sudo caddy validate --config "$CADDYFILE" --adapter caddyfile >/dev/null 2>&1
sudo systemctl reload caddy

paso "Despliegue continuo"
como_cedis '
mkdir -p ~/.config/systemd/user
ln -sf ~/reto1/infra/systemd/reto1-actualizar@.service ~/reto1/infra/systemd/reto1-actualizar@.timer ~/.config/systemd/user/
systemctl --user daemon-reload'
if [[ "${ACTIVAR:-0}" == 1 ]]; then
  como_cedis 'systemctl --user enable --now reto1-actualizar@produccion.timer reto1-actualizar@staging.timer'
  echo "  timers activos"
else
  echo "  timers instalados; se activan con ACTIVAR=1 (ver infra/README.md)"
fi

paso "Listo"
