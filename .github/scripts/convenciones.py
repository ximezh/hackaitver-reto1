"""Revisa que un PR siga las convenciones del equipo (docs/scrum.md · Coordinación entre áreas).

- Rama: `<área>-<tipo>/sprint<N>`.
- Título del PR y asunto de cada commit: Conventional Commits con el área como alcance.
- Archivos: cada área edita solo lo suyo; `design/` es de solo lectura.

Un PR de `dev` a `main` (cierre de sprint) solo revisa el título.
Lee los datos del PR de variables de entorno y los cambios con git.
"""

import os
import re
import subprocess
import sys
from dataclasses import dataclass, field

AREAS = ("front", "back", "devops")
TIPOS = ("feat", "fix", "test", "docs", "refactor", "style", "chore", "ci")
ETIQUETA_DISENO = "diseno-autorizado"

RAMA = re.compile(
    rf"^(?P<area>{'|'.join(AREAS)})-(?P<tipo>{'|'.join(TIPOS)})/sprint(?P<sprint>\d+)$"
)
CONVENCIONAL = re.compile(rf"^(?P<tipo>{'|'.join(TIPOS)})(\((?P<alcance>[a-z0-9-]+)\))?!?: \S.*$")

# Del más específico al más general: gana la primera coincidencia.
DUENOS = (
    ("design/", "diseno"),
    ("front/src/api/", "devops"),
    ("front/vite.config.js", "devops"),
    ("front/.env.example", "devops"),
    ("front/Dockerfile", "devops"),
    ("front/.dockerignore", "devops"),
    ("front/nginx.conf.template", "devops"),
    ("back/Dockerfile", "devops"),
    ("back/.dockerignore", "devops"),
    (".github/", "devops"),
    ("infra/", "devops"),
    ("tools/", "devops"),
    ("docs/scrum/devops.md", "devops"),
    ("back/", "back"),
    ("compose.yaml", "back"),
    ("docs/api/", "back"),
    ("docs/scrum/back.md", "back"),
    ("front/", "front"),
    ("docs/scrum/front.md", "front"),
    ("docs/scrum.md", "compartido"),
    ("docs/AGENTE.md", "compartido"),
    ("CLAUDE.md", "compartido"),
    ("README.md", "compartido"),
    (".gitignore", "compartido"),
    (".gitattributes", "compartido"),
    (".editorconfig", "compartido"),
    (".claude/", "compartido"),
    (".vscode/", "compartido"),
)

# DevOps agrega dependencias del front (Axios) solo en el sprint 0.
EXCEPCION_SPRINT0_DEVOPS = ("front/package.json", "front/package-lock.json")


@dataclass
class Resultado:
    errores: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)


def dueno(ruta: str) -> str | None:
    for prefijo, area in DUENOS:
        if ruta == prefijo or (prefijo.endswith("/") and ruta.startswith(prefijo)):
            return area
    return None


def revisar_titulo(titulo: str, area: str | None, res: Resultado) -> None:
    m = CONVENCIONAL.match(titulo)
    if not m:
        res.errores.append(
            f"El título «{titulo}» no sigue Conventional Commits: `tipo(alcance): descripción`."
        )
    elif area and m.group("alcance") != area:
        res.errores.append(
            f"El título debe llevar el alcance del área: `{m.group('tipo')}({area}): …`."
        )


def revisar_commits(asuntos: list[str], area: str, res: Resultado) -> None:
    for asunto in asuntos:
        m = CONVENCIONAL.match(asunto)
        if not m:
            res.errores.append(f"Commit «{asunto}»: no sigue `tipo({area}): descripción`.")
        elif m.group("alcance") not in (area, "scrum"):
            res.errores.append(f"Commit «{asunto}»: el alcance debe ser `{area}` (o `scrum`).")


def revisar_archivos(
    archivos: list[str], area: str, sprint: int, etiquetas: set[str], res: Resultado
) -> None:
    for ruta in archivos:
        d = dueno(ruta)
        if d == area:
            continue
        if d == "diseno":
            if ETIQUETA_DISENO not in etiquetas:
                res.errores.append(
                    f"`{ruta}`: `design/` es de solo lectura. Si el cambio está autorizado, "
                    f"agrega la etiqueta `{ETIQUETA_DISENO}` al PR."
                )
        elif d == "compartido":
            res.avisos.append(f"`{ruta}` es compartido: el cambio necesita el acuerdo del equipo.")
        elif area == "devops" and sprint == 0 and ruta in EXCEPCION_SPRINT0_DEVOPS:
            res.avisos.append(
                f"`{ruta}`: excepción del sprint 0 para dependencias de DevOps. Avisa a front."
            )
        elif d is None:
            res.errores.append(
                f"`{ruta}` no tiene dueño. Agrégalo a la tabla de propiedad de `docs/scrum.md` "
                "y a `.github/scripts/convenciones.py`."
            )
        else:
            res.errores.append(
                f"`{ruta}` es de `{d}`; una rama de `{area}` no lo edita. "
                f"Abre un issue con la etiqueta `{d}`."
            )


def revisar(
    base: str, rama: str, titulo: str, etiquetas: set[str], archivos: list[str], asuntos: list[str]
) -> Resultado:
    res = Resultado()
    if base == "main":
        if rama != "dev":
            res.errores.append(f"`main` solo recibe PR desde `dev`, no desde `{rama}`.")
        revisar_titulo(titulo, None, res)
        return res

    m = RAMA.match(rama)
    if not m:
        res.errores.append(
            f"La rama «{rama}» no sigue `<área>-<tipo>/sprint<N>`, "
            "por ejemplo `front-feat/sprint1`."
        )
        revisar_titulo(titulo, None, res)
        return res

    area, sprint = m.group("area"), int(m.group("sprint"))
    revisar_titulo(titulo, area, res)
    revisar_commits(asuntos, area, res)
    revisar_archivos(archivos, area, sprint, etiquetas, res)
    return res


def git(*args: str) -> list[str]:
    salida = subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout
    return [linea for linea in salida.splitlines() if linea]


def main() -> int:
    base, rama, sha = os.environ["PR_BASE"], os.environ["PR_HEAD"], os.environ["PR_SHA"]
    titulo = os.environ["PR_TITULO"]
    etiquetas = {e for e in os.environ.get("PR_ETIQUETAS", "").split(",") if e}
    rango = f"origin/{base}...{sha}"
    archivos = git("diff", "--name-only", rango)
    asuntos = git("log", "--no-merges", "--format=%s", f"origin/{base}..{sha}")

    res = revisar(base, rama, titulo, etiquetas, archivos, asuntos)

    lineas = ["## Convenciones del PR", ""]
    for aviso in res.avisos:
        print(f"::warning::{aviso}")
        lineas.append(f"- ⚠️ {aviso}")
    for error in res.errores:
        print(f"::error::{error}")
        lineas.append(f"- ❌ {error}")
    if not res.errores and not res.avisos:
        lineas.append("- ✅ Rama, título, commits y archivos siguen las convenciones.")
    resumen = os.environ.get("GITHUB_STEP_SUMMARY")
    if resumen:
        with open(resumen, "a", encoding="utf-8") as f:
            f.write("\n".join(lineas) + "\n")
    return 1 if res.errores else 0


if __name__ == "__main__":
    sys.exit(main())
