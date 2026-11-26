# Contratos de API · CEDIS Flow

Contratos que publica el back para que DevOps arme los servicios y mocks de `front/src/api/` y el front construya las pantallas sin esperar al back (A-12).

| Sprint | Contrato | Contenido |
|---|---|---|
| 1 | [sprint-1.md](sprint-1.md) | Login, sesión, contraseña temporal y CRUD de productos, proveedores, sucursales y usuarios |
| 2 | `sprint-2.md` (BE-16) | Pedidos, OC, citas, disponibilidad, facturas, bultos y etiquetas |

Si un contrato cambia después de publicarse, el back abre un issue con las etiquetas `front` y `devops`.

## Convenciones

Aplican a todos los contratos.

### Base y formato

- Todas las rutas empiezan con `/api`. En desarrollo, Vite reenvía `/api` al back.
- Cuerpos y respuestas en JSON, UTF-8. Los nombres de campos van en español y en `snake_case`, sin acentos: `contrasena`, `piezas_por_bulto`.
- Los valores fijos (roles, canales, estados) se envían como códigos en minúsculas (`activo`, `oficina`). El front muestra la etiqueta que indica cada contrato.
- Los `id` son enteros. Los folios (`OC-26-…`, `B-…`) son cadenas.
- Pesos en kg y volúmenes en m³, como números JSON: `25.0`, `0.032`.

### Fechas

- Formato ISO 8601 con desfase: `2026-11-25T09:30:00-06:00`.
- La zona horaria de la operación es `America/Mexico_City` (S-06). Las fechas sin hora van como `2026-11-25`.

### Autenticación

- `POST /api/auth/login` devuelve un JWT. Las demás rutas lo piden en el encabezado:

  ```http
  Authorization: Bearer <access_token>
  ```

- El token dura 12 horas, un turno. Al vencer, la API responde `401 token_expirado` y el front regresa al login.
- No hay ruta de cierre de sesión: el front borra el token.
- El front no decodifica el token. El usuario, el rol y el canal se leen de `GET /api/auth/me`.

### Listas

Las listas responden con un objeto, para poder agregar paginación después sin romper el contrato:

```json
{ "items": [ … ], "total": 7 }
```

- `?q=` busca en los campos de texto del registro, sin distinguir mayúsculas ni acentos.
- El orden es el de creación, del más antiguo al más nuevo, salvo que el contrato indique otro.

### Errores

Todo error responde con la misma forma:

```json
{ "detail": "Revisa usuario y contraseña", "code": "credenciales_invalidas" }
```

- `detail` es el texto que se muestra al usuario, tal cual, en el toast o junto al campo.
- `code` es estable: el front decide con `code`, nunca con `detail`.
- Los errores de validación agregan `campos`, con el mensaje de cada campo inválido. `detail` repite el mensaje del primer campo:

  ```json
  {
    "detail": "Completa SKU",
    "code": "validacion",
    "campos": { "sku": "Completa SKU", "kg": "El peso debe ser mayor a 0" }
  }
  ```

| HTTP | `code` | `detail` | Cuándo |
|---|---|---|---|
| 401 | `no_autenticado` | Inicia sesión para continuar | Falta el token o no es válido |
| 401 | `token_expirado` | Tu sesión terminó. Inicia sesión de nuevo | El token venció |
| 403 | `sin_permiso` | No tienes acceso a esta sección | El rol no puede usar la ruta |
| 403 | `cambio_contrasena_requerido` | Cambia tu contraseña para continuar | La contraseña es temporal (R-17) |
| 404 | `no_encontrado` | No encontramos el registro | El `id` o folio no existe |
| 405 | `metodo_no_permitido` | Esta acción no está disponible | La ruta existe, pero no con ese método |
| 409 | según el caso | según el caso | Duplicados, recurso ocupado o conflicto de estado |
| 409 | `conflicto` | No se pudo guardar porque choca con otro registro | Restricción de la base sin un `code` propio |
| 422 | `validacion` | Mensaje del primer campo | Cuerpo o parámetros inválidos |
| 500 | `error_interno` | Algo salió mal. Intenta de nuevo | Error no previsto; el detalle queda en el log |

Cada contrato lista los `code` propios de sus rutas.

### Folios

| Folio | Formato | Ejemplo |
|---|---|---|
| Orden de compra | `OC-<aa>-<n>`, con el año de la operación en México | `OC-26-1182` |
| Bulto | `B-<n>` | `B-0003` |
| Tarima | `T-<clave de sucursal>-<n>`, numerada por sucursal | `T-07-03` |
| Embarque | `EMB-<n>` | `EMB-0412` |
| Factura | La captura el proveedor; el back no la genera (R-04) | `FAC-A-20418` |

- El número tiene al menos 4 dígitos (2 en las tarimas) y crece si hace falta: `B-10000`.
- No se repiten. Puede haber huecos si una operación se cancela.
