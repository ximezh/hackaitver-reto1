#!/usr/bin/env bash
# Despliegue continuo de un entorno (DO-13, A-15). Lo corre cada minuto un timer de systemd en la
# instancia (infra/systemd/). No necesita que GitHub entre por SSH: consulta el repositorio.
#
#   infra/actualizar.sh produccion    # sigue a `main`
#   infra/actualizar.sh staging       # sigue a `dev`
#
# Pasos:
#   1. Si la rama del entorno no avanzó desde el último despliegue, termina.
#   2. Espera las imágenes `sha-<commit>` que publica el job «Publicar imágenes» del CI solo cuando
#      pasa. Si el CI falló, nunca aparecen y el entorno sigue con la versión anterior.
#   3. Corre las migraciones, levanta la versión nueva y revisa /api/health a través de Nginx.
#   4. Si algo falla, vuelve a levantar la versión anterior.
#
# Variables opcionales: REPO (clon del repositorio, ~/reto1), REGISTRO (ghcr.io/ximezh),
# ESTADO (~/.local/state/reto1), RAMA (para probar con otra rama) y ESPERA_SALUD (segundos, 90).
set -euo pipefail

ENTORNO="${1:?Uso: actualizar.sh produccion|staging}"
case "$ENTORNO" in
  produccion) RAMA_POR_DEFECTO=main ;;
  staging) RAMA_POR_DEFECTO=dev ;;
  *) echo "Entorno desconocido: $ENTORNO" >&2; exit 2 ;;
esac

REPO="${REPO:-$HOME/reto1}"
REGISTRO="${REGISTRO:-ghcr.io/ximezh}"
ESTADO="${ESTADO:-$HOME/.local/state/reto1}/$ENTORNO"
RAMA="${RAMA:-$RAMA_POR_DEFECTO}"
ESPERA_SALUD="${ESPERA_SALUD:-90}"
ARCHIVO_ENTORNO="$REPO/infra/entornos/$ENTORNO.env"

mkdir -p "$ESTADO"
exec 9>"$ESTADO/candado"
flock -n 9 || { echo "Ya hay un despliegue de $ENTORNO en curso"; exit 0; }

registro() { echo "[$ENTORNO] $*"; }

[[ -f "$ARCHIVO_ENTORNO" ]] || { registro "Falta $ARCHIVO_ENTORNO"; exit 1; }

git -C "$REPO" fetch --quiet origin "$RAMA"
objetivo=$(git -C "$REPO" rev-parse "origin/$RAMA")
actual=$(cat "$ESTADO/desplegado" 2>/dev/null || true)
[[ "$objetivo" == "$actual" ]] && exit 0
[[ "$objetivo" == "$(cat "$ESTADO/fallido" 2>/dev/null || true)" ]] && exit 0

imagen() { echo "$REGISTRO/hackaitver-reto1-$1:sha-$2"; }

traer() {
  local img
  for parte in back front; do
    img=$(imagen "$parte" "$1")
    podman image exists "$img" || podman pull --quiet "$img" >/dev/null 2>&1 || return 1
  done
}

# Compose de la versión indicada, tomado del propio commit.
compose_de() {
  local destino="$ESTADO/compose-$1.yaml"
  git -C "$REPO" show "$1:infra/compose.entorno.yaml" >"$destino"
  echo "$destino"
}

compose() {
  local version="$1"
  shift
  IMAGEN_BACK=$(imagen back "$version") IMAGEN_FRONT=$(imagen front "$version") \
    podman compose -f "$(compose_de "$version")" --env-file "$ARCHIVO_ENTORNO" "$@"
}

sano() {
  local limite=$((SECONDS + ESPERA_SALUD))
  while ((SECONDS < limite)); do
    if podman exec "reto1-$ENTORNO-front-1" wget -q -O - http://127.0.0.1/api/health 2>/dev/null |
      grep -q '"database":"ok"'; then
      return 0
    fi
    sleep 3
  done
  return 1
}

if ! traer "$objetivo"; then
  registro "Las imágenes de ${objetivo:0:7} aún no están publicadas (o su CI falló). Se reintenta en el siguiente ciclo."
  exit 0
fi

registro "Desplegando ${objetivo:0:7} (antes: ${actual:0:7})"
if compose "$objetivo" up -d db &&
  compose "$objetivo" run --rm --no-deps -T back alembic upgrade head </dev/null &&
  compose "$objetivo" up -d &&
  sano; then
  echo "$objetivo" >"$ESTADO/desplegado"
  registro "Listo: ${objetivo:0:7}"
  exit 0
fi

registro "Falló el despliegue de ${objetivo:0:7}"
if [[ -n "$actual" ]]; then
  registro "Volviendo a ${actual:0:7}"
  compose "$actual" up -d && sano && registro "Se mantiene ${actual:0:7}"
fi
# Se recuerda el intento fallido para no repetirlo cada minuto; un commit nuevo lo vuelve a intentar.
echo "$objetivo" >"$ESTADO/fallido"
[[ -n "$actual" ]] && echo "$actual" >"$ESTADO/desplegado"
exit 1
