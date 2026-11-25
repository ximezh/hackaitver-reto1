# Instrucciones para agentes · CEDIS Flow

Estas instrucciones aplican a cualquier agente de IA que trabaje en este repositorio (Claude Code, Codex, Cursor u otro) y a los desarrolladores que lo usan.

## 1. Antes de empezar: identifica tu área

El equipo son tres desarrolladores, cada uno con su agente. Al iniciar una sesión, confirma con el usuario quién es y trabaja **solo** en su área.

| Área | Responsable | Abarca | Plan |
|---|---|---|---|
| `front` | Ximena Zaleta | UI/UX, interfaces, componentes y layouts | [scrum/front.md](scrum/front.md) |
| `back` | Jesus Vazquez | APIs, endpoints, controladores, modelos e instancia de PostgreSQL en Podman | [scrum/back.md](scrum/back.md) |
| `devops` | Luis Daniel Morales | Axios, conexión front ↔ back, CORS, CI/CD, despliegue e instancia en AWS | [scrum/devops.md](scrum/devops.md) |

El plan general (reglas de negocio, decisiones, hallazgos, preguntas, DoR y DoD) está en [scrum.md](scrum.md).

## 2. Regla del prototipo

**El diseño del prototipo no se modifica.** La interfaz debe ser idéntica a `design/CEDIS Flow/`.

- `design/` es de solo lectura. No edites, muevas ni borres nada ahí.
- No «mejores», reinterpretes ni rediseñes pantallas, textos, colores, tamaños, espacios, íconos, ilustraciones o animaciones.
- Solo cambia un detalle de diseño si Ximena, Jesus o Luis Daniel lo piden de forma explícita. Anótalo en «Cambios de diseño autorizados» de `scrum.md`. Antes de construir una pantalla, revisa esa tabla.
- Las pantallas nuevas autorizadas (perfil, contraseña, avisos, búsqueda, pestañas móviles) usan solo los tokens, componentes, íconos e ilustraciones del prototipo, y Ximena aprueba su diseño antes de programarlas.
- Si encuentras un error o un hueco en el prototipo, no lo resuelvas por tu cuenta: revisa «Hallazgos» y «Preguntas» en `scrum.md`, aplica el criterio por defecto o pregunta al usuario.
- Para comparar, usa el visor local del prototipo (`tools/prototipo/`, historia DO-06).

## 3. No pisar a otras áreas

- Edita solo los archivos de tu área según la tabla «Propiedad de archivos» de `scrum.md`.
- Si necesitas algo de otra área, no lo hagas tú: abre un issue con la etiqueta del área (`front`, `back`, `devops`) y la historia que lo necesita.
- **Contrato primero:** el back publica los contratos en `docs/api/`; DevOps crea los servicios y mocks en `front/src/api/`; el front consume solo `@/api`.
- Lo que surja a mitad de sprint va al backlog de tu plan, no al sprint en curso.

## 4. Flujo de cada tarea

1. **Analizar:** lee la historia en el plan de tu área y el código relacionado.
2. **Crear el código:** solo lo que pide la historia, sin adelantar otras.
3. **Verificar:** corre lint, pruebas y build de lo que tocaste. Si hay interfaz, revísala en el navegador contra el prototipo.
4. **Proponer el commit:** muestra el mensaje exacto, los archivos, qué se comprobó y qué quedó sin comprobar. **Detente aquí.**
5. **Subir:** haz commit y push solo después de la confirmación del usuario. Cada confirmación vale solo para ese commit.

Nunca hagas `force push`, reescribas historial, borres ramas ni hagas merge de PR sin que se pida. Los PR solo se abren; el merge lo hace el usuario en GitHub.

## 5. Ramas, commits y PR

**Ramas:** `<área>-<tipo>/sprint<N>`, desde `dev`. Una por área y sprint.

```text
front-feat/sprint1    back-feat/sprint2    devops-ci/sprint0    back-fix/sprint3
```

Tipos: `feat`, `fix`, `test`, `docs`, `refactor`, `style`, `chore`, `ci`.

**Commits:** Conventional Commits en español, verbo en tercera persona, en minúsculas, sin punto final, unos 70 caracteres. El alcance es el área.

```text
feat(front): agrega la pantalla de caseta con check-in y check-out
feat(back): impide empalmes de citas con una restricción exclude
ci(devops): valida el nombre de rama y el título del pr
docs(scrum): cierra el sprint 1 de front
```

- Una historia por commit; las pruebas van en el mismo commit que su código.
- No agregues referencias a IA ni a agentes en commits, ramas, PR, comentarios o código: nada de `Co-Authored-By`, `Generated with` ni similares.

**PR:** uno por área y sprint hacia `dev`, cuando las historias estén subidas. Título con la convención de commits, por ejemplo `feat(front): login, oficina y catálogos (sprint 1)`. Descripción:

```markdown
## Tareas
FE-10 · FE-11 · FE-12

## Qué cambia
- **FE-10:** qué se hizo y qué decisión importa.

## Cómo probarlo
Comandos y recorrido en la aplicación, con el número de pruebas.

## Pendientes
Lo bloqueado o sin verificar, dicho de forma directa.
```

Al cerrar un sprint, marca el avance en la tabla «Avance» de tu plan con un commit `docs(scrum): …`.

## 6. Definition of Done

- Se cumplen todos los criterios de la historia.
- Pasan lint, pruebas y build en local y en CI.
- Front: la pantalla queda igual al prototipo; la captura lado a lado va en el PR.
- Back: las reglas de negocio tienen pruebas contra PostgreSQL y el endpoint coincide con el contrato.
- No se suben secretos, `.env`, bases de datos ni datos reales.

## 7. Stack y comandos

| Parte | Stack | Carpeta |
|---|---|---|
| Front | Vue 3 (JavaScript), Vite, Vue Router, Pinia, Vitest, ESLint + Oxlint, Prettier | `front/` |
| Back | Python 3.13 con uv, FastAPI, SQLAlchemy 2, Alembic, pytest, Ruff | `back/` |
| Base | PostgreSQL 17 en Podman (`compose.yaml`) | raíz |

```bash
# Base de datos
podman compose up -d            # o: docker compose up -d

# Back (en back/)
uv sync
uv run ruff check . && uv run ruff format --check .
uv run pytest
uv run alembic upgrade head
uv run fastapi dev app/main.py

# Front (en front/)
npm install
npm run lint && npm test && npm run build
npm run dev
```

## 8. Archivos de agentes

`docs/AGENTE.md` (este archivo), `CLAUDE.md` (en la raíz) y `.claude/` se versionan. Si cambias estas instrucciones, hazlo con acuerdo del equipo.
