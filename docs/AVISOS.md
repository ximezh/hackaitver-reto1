# Sistema de avisos entre áreas

Cada área tiene un buzón con los avisos que le dejan las otras áreas cuando un cambio suyo la afecta. Los leen los desarrolladores y sus agentes.

| Buzón | Lo lee | Le escriben |
|---|---|---|
| [AVISOS-front.md](AVISOS-front.md) | Ximena y su agente | Back y DevOps |
| [AVISOS-back.md](AVISOS-back.md) | Jesus y su agente | Front y DevOps |
| [AVISOS-devops.md](AVISOS-devops.md) | Luis Daniel y su agente | Front y Back |

## Cuándo dejar un aviso

Cada desarrollador, o su agente, deja un aviso en el buzón de otra área **en el mismo commit** del cambio que la afecta. Por ejemplo:

- Cambia un contrato de API, una ruta, un campo o un código de error.
- Se agrega o cambia una dependencia, variable de entorno, comando o servicio que la otra área usa.
- Cambian los mocks, el CI, las convenciones o los archivos de contenedor.
- Se publica algo que la otra área estaba esperando (un contrato, un endpoint, un servicio).
- Se toma una decisión que cambia cómo trabaja la otra área.

Un aviso informa. Si se necesita que la otra área **haga trabajo nuevo**, además se abre un issue con su etiqueta (`front`, `back`, `devops`).

## Formato

Los avisos se agregan al inicio de la sección «Pendientes» del buzón, el más nuevo arriba.

```markdown
### AV-DO-004 · 2026-11-25 · de devops · Pendiente
- **Qué cambió:** una o dos frases.
- **Qué tienes que hacer:** acción concreta, o «Nada, solo para que lo sepas».
- **Referencia:** historia, commit, PR o archivo.
```

- **ID:** `AV-<área que lo emite>-<número>`, con `FE`, `BE` o `DO`. Cada área numera los suyos, así dos ramas no chocan.
- **Estado:** `Pendiente` o `Atendido`. Solo el área dueña del buzón cambia el estado y mueve el aviso a «Atendidos».

## Cómo los revisan los agentes

Al iniciar una sesión y antes de cada tarea, el agente revisa el buzón de su área en `dev` y en su rama:

```bash
git fetch origin
git log --oneline -5 origin/dev -- docs/AVISOS-<área>.md   # ¿llegaron avisos nuevos?
git show origin/dev:docs/AVISOS-<área>.md                  # leer el buzón
```

Si hay avisos `Pendiente`, el agente los resume al usuario antes de seguir, los atiende o los anota en el backlog del plan de su área, y los marca `Atendido` en un commit `docs(<área>): atiende avisos …`.
