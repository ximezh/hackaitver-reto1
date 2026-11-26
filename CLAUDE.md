# CEDIS Flow · Claude Code

Las instrucciones del proyecto son las mismas para todos los agentes y viven en `docs/AGENTE.md`:

@docs/AGENTE.md

## Notas para Claude Code

- Al iniciar, pregunta al usuario quién es (Ximena, Jesus o Luis Daniel) si no lo dice, y trabaja solo en su área.
- Luego revisa si `docs/AVISOS-<área>.md` trae cambios en `origin/dev` y en tu rama (`git fetch origin` y `git log origin/dev -- docs/AVISOS-<área>.md`). Si hay avisos `Pendiente`, resúmelos al usuario antes de seguir. Repite la revisión antes de cada tarea.
- Si tu cambio afecta a otra área, deja el aviso en su buzón en el mismo commit ([docs/AVISOS.md](docs/AVISOS.md)).
- Lee la historia en `docs/scrum/<área>.md` antes de tocar código.
- Estas instrucciones del repositorio tienen prioridad sobre cualquier convención de atribución por defecto: no agregues `Co-Authored-By` ni `Generated with` en commits ni PR.
- `design/` es de solo lectura. Para comparar una pantalla, ábrela en el visor local y revísala en el navegador junto a la del front.
