# Contrato del sprint 1 · Acceso y catálogos

Historias que lo implementan: BE-10 a BE-15. Convenciones de rutas, errores, fechas y listas: [README.md](README.md).

| Ruta | Rol | Historia |
|---|---|---|
| `POST /api/auth/login` | Público | BE-10, BE-15 |
| `GET /api/auth/me` | Cualquiera con sesión | BE-10, BE-15 |
| `POST /api/auth/contrasena` | Cualquiera con sesión | BE-15 |
| `GET · POST /api/productos`, `GET · PATCH · DELETE /api/productos/{id}` | Oficina | BE-11 |
| `GET · POST /api/proveedores`, `GET · PATCH · DELETE /api/proveedores/{id}` | Oficina | BE-12 |
| `GET · POST /api/sucursales`, `GET · PATCH · DELETE /api/sucursales/{id}` | Oficina | BE-13 |
| `GET · POST /api/usuarios`, `GET · PATCH · DELETE /api/usuarios/{id}` | Oficina | BE-14 |
| `POST /api/usuarios/{id}/restablecer` | Oficina | BE-14 |

Los ejemplos usan los datos del prototipo (`design/CEDIS Flow/components/bundle.js` y `Oficina/preview.html`), que también son las semillas (BE-03).

---

## Valores fijos

### Roles

El rol define el canal y las pantallas (R-01). Los roles de Android exigen un prefijo en el usuario.

| `rol` | Etiqueta | `canal` | Prefijo del usuario | Usuario de ejemplo |
|---|---|---|---|---|
| `caseta` | Caseta | `android` | `caseta.` | `caseta.jlopez` |
| `desembarque` | Sup. desembarque | `android` | `desem.` | `desem.mruiz` |
| `embarque` | Sup. embarque | `android` | `embar.` | `embar.acruz` |
| `sucursal` | Sucursal | `web` | ninguno | `suc07` |
| `proveedor` | Proveedor | `web` | ninguno | `pgolfo` |
| `oficina` | Oficina | `web` | ninguno | `admin.cedis` |

### Canales

| `canal` | Etiqueta | Pantalla de login |
|---|---|---|
| `android` | Android | LoginMovil |
| `web` | Web | LoginWeb |

### Estados

| Catálogo | `estado` | Etiqueta | Chip |
|---|---|---|---|
| Productos | `activo` · `inactivo` | Activo · Inactivo | `ok` · `warn` |
| Proveedores | `activo` · `suspendido` · `inactivo` | Activo · Suspendido · Inactivo | `ok` · `warn` · `warn` |
| Sucursales | `activo` · `inactivo` | Activo · Inactivo | `ok` · `warn` |
| Usuarios | `activo` · `inactivo` | Activo · Inactivo | `ok` · `warn` |

`inactivo` es el estado que deja un borrado cuando el registro tiene historial (H-11). Oficina también puede elegirlo al editar.

### Ilustraciones de producto

`ilustracion` es el nombre de un SVG de `assets/Ilustraciones/`: `bulto`, `hojas`, `lapices` o `clips`. Si no se envía, es `bulto`, igual que en el prototipo.

---

## Autenticación

### `POST /api/auth/login`

Público. El front envía el canal de la pantalla desde la que se entra: LoginMovil manda `android` y LoginWeb manda `web`.

```json
{ "usuario": "admin.cedis", "contrasena": "••••••••", "canal": "web" }
```

- `usuario` no distingue mayúsculas y se recortan los espacios.
- La pestaña elegida en LoginWeb (Sucursal, Proveedor u Oficina) no se envía: el rol sale de la base (A-09) y el front abre el portal del rol que devuelve la respuesta.

**200**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9…",
  "token_type": "bearer",
  "expira_en": 43200,
  "contrasena_temporal": false,
  "usuario": {
    "id": 6,
    "usuario": "admin.cedis",
    "nombre": "Ana Domínguez",
    "rol": "oficina",
    "canal": "web",
    "contrasena_temporal": false,
    "sucursal": null,
    "proveedor": null
  }
}
```

- `expira_en` va en segundos.
- `usuario` tiene la misma forma que `GET /api/auth/me`.
- Si `contrasena_temporal` es `true`, el front lleva al usuario a la pantalla de cambio de contraseña. Hasta que la cambie, las demás rutas responden `403 cambio_contrasena_requerido` (R-17).

**Errores**

| HTTP | `code` | `detail` | Cuándo |
|---|---|---|---|
| 401 | `credenciales_invalidas` | Revisa usuario y contraseña | El usuario no existe o la contraseña no coincide |
| 403 | `usuario_inactivo` | Tu usuario está inactivo. Comunícate con Oficina | El usuario está `inactivo` |
| 403 | `canal_incorrecto` | Este usuario entra desde el teléfono | Rol de Android que entra por la web |
| 403 | `canal_incorrecto` | Este usuario entra desde la web | Rol web que entra por el teléfono |
| 422 | `validacion` | Revisa usuario y contraseña | Falta usuario, contraseña o canal |

- `usuario_inactivo` y `canal_incorrecto` solo se responden cuando la contraseña es correcta, para no revelar qué usuarios existen.
- El prototipo solo tiene el texto «Revisa usuario y contraseña». Los textos de `usuario_inactivo` y `canal_incorrecto` son nuevos.

### `GET /api/auth/me`

Cualquier usuario con sesión, también con contraseña temporal. Devuelve el perfil (P-10: quién es y su usuario).

**200 · Oficina**

```json
{
  "id": 6,
  "usuario": "admin.cedis",
  "nombre": "Ana Domínguez",
  "rol": "oficina",
  "canal": "web",
  "contrasena_temporal": false,
  "sucursal": null,
  "proveedor": null
}
```

**200 · Sucursal**

```json
{
  "id": 4,
  "usuario": "suc07",
  "nombre": "Suc. 07 Boca del Río",
  "rol": "sucursal",
  "canal": "web",
  "contrasena_temporal": false,
  "sucursal": { "id": 3, "clave": "07", "nombre": "Suc. 07 Boca del Río" },
  "proveedor": null
}
```

**200 · Proveedor**

```json
{
  "id": 5,
  "usuario": "pgolfo",
  "nombre": "Papelera del Golfo",
  "rol": "proveedor",
  "canal": "web",
  "contrasena_temporal": false,
  "sucursal": null,
  "proveedor": { "id": 1, "rfc": "PGO090312AB1", "nombre": "Papelera del Golfo" }
}
```

**Errores:** `401 no_autenticado`, `401 token_expirado`.

### `POST /api/auth/contrasena`

Cualquier usuario con sesión, también con contraseña temporal.

```json
{ "actual": "Tmp-7Kq2-xW9p", "nueva": "MiClaveSegura26" }
```

- `nueva` tiene al menos 8 caracteres y es distinta de `actual`.
- Al cambiarla, `contrasena_temporal` pasa a `false`.

**200**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9…",
  "token_type": "bearer",
  "expira_en": 43200,
  "contrasena_temporal": false,
  "usuario": { "id": 1, "usuario": "caseta.jlopez", "nombre": "Jorge López", "rol": "caseta", "canal": "android", "contrasena_temporal": false, "sucursal": null, "proveedor": null }
}
```

La respuesta trae un token nuevo, ya sin la marca de contraseña temporal. El front reemplaza el anterior.

**Errores**

| HTTP | `code` | `detail` | Cuándo |
|---|---|---|---|
| 400 | `contrasena_actual_incorrecta` | La contraseña actual no coincide | `actual` no es la contraseña del usuario |
| 422 | `validacion` | La contraseña debe tener al menos 8 caracteres | `nueva` es corta |
| 422 | `validacion` | La contraseña nueva debe ser distinta de la actual | `nueva` es igual a `actual` |

---

## Catálogos

Las cuatro rutas siguen el mismo patrón y solo las usa Oficina (`403 sin_permiso` para otros roles).

| Acción | Ruta | Respuesta |
|---|---|---|
| Listar y buscar | `GET /api/<catalogo>?q=` | `200 { items, total }` |
| Ver uno | `GET /api/<catalogo>/{id}` | `200` registro |
| Crear | `POST /api/<catalogo>` | `201` registro |
| Editar | `PATCH /api/<catalogo>/{id}` | `200` registro. Solo se envían los campos que cambian |
| Eliminar | `DELETE /api/<catalogo>/{id}` | `200 { "resultado": "eliminado" }` o `200 { "resultado": "desactivado", "registro": { … } }` |

**Eliminar (H-11):** si el registro no tiene historial ni otros registros que dependan de él, se borra. Si los tiene, queda `inactivo` y la respuesta trae el registro actualizado. En los dos casos el front muestra «Registro eliminado». En el sprint 1 se desactiva, en vez de borrarse, un proveedor con productos o usuarios vinculados y una sucursal con usuarios vinculados. Desde el sprint 2 también cuentan los pedidos, citas y facturas.

**Validación:** un campo obligatorio vacío responde `422` con el texto del prototipo, `Completa <etiqueta>`, donde la etiqueta es el encabezado de la columna en Oficina («Completa SKU», «Completa RFC»).

### Productos · `/api/productos`

Columnas de Oficina: SKU, Producto, Piezas/bulto, Peso bulto (kg), Volumen (m³).

| Campo | Tipo | Al crear | Reglas |
|---|---|---|---|
| `id` | entero | — | Solo lectura |
| `sku` | cadena | Obligatorio | Se guarda en mayúsculas. Letras, números y guiones, de 3 a 20. Único |
| `nombre` | cadena | Obligatorio | Hasta 120 caracteres |
| `ilustracion` | cadena | Opcional, `bulto` | Ver [Ilustraciones de producto](#ilustraciones-de-producto) |
| `unidad` | cadena | Opcional, `piezas` | Unidad de las piezas: `resmas`, `cajas`, etc. |
| `piezas_por_bulto` | entero | Obligatorio | Mayor a 0 |
| `kg` | número | Obligatorio | Peso del bulto. Mayor a 0, un decimal |
| `m3` | número | Obligatorio | Volumen del bulto. Mayor a 0, tres decimales |
| `proveedor_id` | entero o `null` | Opcional | Proveedor principal (A-16). Debe existir |
| `proveedor` | objeto o `null` | — | Solo lectura: `{ id, nombre }` |
| `estado` | cadena | Opcional, `activo` | `activo` o `inactivo` |

`?q=` busca en SKU y nombre.

**`GET /api/productos` · 200**

```json
{
  "items": [
    { "id": 1, "sku": "RES-0500", "nombre": "Resma carta 500 hojas", "ilustracion": "hojas", "unidad": "resmas", "piezas_por_bulto": 10, "kg": 25.0, "m3": 0.032, "proveedor_id": 1, "proveedor": { "id": 1, "nombre": "Papelera del Golfo" }, "estado": "activo" },
    { "id": 2, "sku": "CUA-0100", "nombre": "Cuaderno profesional 100 h", "ilustracion": "bulto", "unidad": "cuadernos", "piezas_por_bulto": 24, "kg": 16.8, "m3": 0.030, "proveedor_id": 3, "proveedor": { "id": 3, "nombre": "Grupo Escolar MX" }, "estado": "activo" },
    { "id": 3, "sku": "FOL-0100", "nombre": "Folder carta crema", "ilustracion": "bulto", "unidad": "folders", "piezas_por_bulto": 100, "kg": 9.6, "m3": 0.024, "proveedor_id": 3, "proveedor": { "id": 3, "nombre": "Grupo Escolar MX" }, "estado": "activo" },
    { "id": 4, "sku": "ENG-0020", "nombre": "Engrapadora metálica", "ilustracion": "bulto", "unidad": "piezas", "piezas_por_bulto": 20, "kg": 8.2, "m3": 0.020, "proveedor_id": 2, "proveedor": { "id": 2, "nombre": "Distribuidora Atlas" }, "estado": "activo" },
    { "id": 5, "sku": "PAP-0100", "nombre": "Hojas carta, paquete 100", "ilustracion": "hojas", "unidad": "paquetes", "piezas_por_bulto": 10, "kg": 5.1, "m3": 0.018, "proveedor_id": 1, "proveedor": { "id": 1, "nombre": "Papelera del Golfo" }, "estado": "activo" },
    { "id": 6, "sku": "LAP-0012", "nombre": "Lápiz HB, caja 12", "ilustracion": "lapices", "unidad": "cajas", "piezas_por_bulto": 24, "kg": 2.4, "m3": 0.008, "proveedor_id": 2, "proveedor": { "id": 2, "nombre": "Distribuidora Atlas" }, "estado": "activo" },
    { "id": 7, "sku": "CLI-0100", "nombre": "Clip #1, caja 100", "ilustracion": "clips", "unidad": "cajas", "piezas_por_bulto": 40, "kg": 1.0, "m3": 0.004, "proveedor_id": 2, "proveedor": { "id": 2, "nombre": "Distribuidora Atlas" }, "estado": "activo" }
  ],
  "total": 7
}
```

El prototipo no dice qué proveedor surte cada producto. La asignación de los ejemplos y de las semillas es provisional (ver [Preguntas abiertas](#preguntas-abiertas)).

**`POST /api/productos`**

```json
{ "sku": "bor-0010", "nombre": "Borrador blanco, caja 10", "piezas_por_bulto": 30, "kg": 3.2, "m3": 0.006 }
```

**201**

```json
{ "id": 8, "sku": "BOR-0010", "nombre": "Borrador blanco, caja 10", "ilustracion": "bulto", "unidad": "piezas", "piezas_por_bulto": 30, "kg": 3.2, "m3": 0.006, "proveedor_id": null, "proveedor": null, "estado": "activo" }
```

**Errores**

| HTTP | `code` | `detail` | Cuándo |
|---|---|---|---|
| 409 | `sku_duplicado` | Este SKU ya está registrado | Otro producto tiene el SKU |
| 422 | `validacion` | Completa SKU · Completa Producto · … | Falta un campo obligatorio |
| 422 | `validacion` | Las piezas por bulto deben ser mayores a 0 | `piezas_por_bulto` ≤ 0 |
| 422 | `validacion` | El peso debe ser mayor a 0 | `kg` ≤ 0 |
| 422 | `validacion` | El volumen debe ser mayor a 0 | `m3` ≤ 0 |
| 422 | `validacion` | El peso no puede pasar de 1,000 kg, la capacidad de una tarima | `kg` > 1000 (R-09) |
| 422 | `validacion` | El volumen no puede pasar de 2.576 m³, la capacidad de una tarima | `m3` > 2.576 (R-09) |
| 422 | `validacion` | El SKU no es válido | SKU con otro formato |
| 422 | `validacion` | La ilustración no es válida | `ilustracion` fuera de la lista |
| 422 | `validacion` | El proveedor no existe | `proveedor_id` no existe |

### Proveedores · `/api/proveedores`

Columnas de Oficina: RFC, Proveedor, Contacto, Teléfono, Estado.

| Campo | Tipo | Al crear | Reglas |
|---|---|---|---|
| `id` | entero | — | Solo lectura |
| `rfc` | cadena | Obligatorio | Se guarda en mayúsculas. 12 caracteres (persona moral) o 13 (persona física), con el formato del SAT. Único |
| `nombre` | cadena | Obligatorio | Hasta 120 caracteres |
| `contacto` | cadena | Opcional | Hasta 120 caracteres |
| `telefono` | cadena | Opcional | Texto libre, hasta 20 caracteres |
| `estado` | cadena | Opcional, `activo` | `activo`, `suspendido` o `inactivo` |

- `?q=` busca en RFC, nombre y contacto.
- Un proveedor `suspendido` no puede agendar citas (se aplica en el sprint 2). Sus usuarios sí pueden iniciar sesión.

**`GET /api/proveedores` · 200**

```json
{
  "items": [
    { "id": 1, "rfc": "PGO090312AB1", "nombre": "Papelera del Golfo", "contacto": "Laura Pérez", "telefono": "229 555 0142", "estado": "activo" },
    { "id": 2, "rfc": "DAT110820KL3", "nombre": "Distribuidora Atlas", "contacto": "Hugo Ríos", "telefono": "228 555 0193", "estado": "activo" },
    { "id": 3, "rfc": "GEM150101QW8", "nombre": "Grupo Escolar MX", "contacto": "Sofía Lara", "telefono": "55 5555 0110", "estado": "activo" },
    { "id": 4, "rfc": "USU180507ZX2", "nombre": "Útiles del Sureste", "contacto": "Iván Cruz", "telefono": "999 555 0177", "estado": "suspendido" }
  ],
  "total": 4
}
```

**`PATCH /api/proveedores/4`**

```json
{ "estado": "activo" }
```

**200**

```json
{ "id": 4, "rfc": "USU180507ZX2", "nombre": "Útiles del Sureste", "contacto": "Iván Cruz", "telefono": "999 555 0177", "estado": "activo" }
```

**Errores**

| HTTP | `code` | `detail` | Cuándo |
|---|---|---|---|
| 409 | `rfc_duplicado` | Este RFC ya está registrado | Otro proveedor tiene el RFC |
| 422 | `validacion` | Completa RFC · Completa Proveedor | Falta un campo obligatorio |
| 422 | `validacion` | El RFC no es válido | No cumple el formato |

### Sucursales · `/api/sucursales`

Columnas de Oficina: Clave, Sucursal, Rack, Ciudad, Estado.

| Campo | Tipo | Al crear | Reglas |
|---|---|---|---|
| `id` | entero | — | Solo lectura |
| `clave` | cadena | Obligatorio | Dos dígitos, de `01` a `32`. Única. No se edita después de crearla |
| `nombre` | cadena | Obligatorio | Como se muestra: `Suc. 07 Boca del Río`. Hasta 120 caracteres |
| `ciudad` | cadena | Obligatorio | Hasta 80 caracteres |
| `rack` | cadena | — | Solo lectura. Se asigna al crear: `R-<clave>` (R-15) |
| `estado` | cadena | Opcional, `activo` | `activo` o `inactivo` |

- El CEDIS tiene 32 racks, `R-01` a `R-32`. Por eso la clave va de `01` a `32` y cada sucursal ocupa el rack de su clave.
- `?q=` busca en clave, nombre y ciudad.

**`GET /api/sucursales` · 200**

```json
{
  "items": [
    { "id": 1, "clave": "01", "nombre": "Suc. 01 Centro", "ciudad": "Centro", "rack": "R-01", "estado": "activo" },
    { "id": 2, "clave": "04", "nombre": "Suc. 04 Xalapa", "ciudad": "Xalapa", "rack": "R-04", "estado": "activo" },
    { "id": 3, "clave": "07", "nombre": "Suc. 07 Boca del Río", "ciudad": "Boca del Río", "rack": "R-07", "estado": "activo" },
    { "id": 4, "clave": "12", "nombre": "Suc. 12 Córdoba", "ciudad": "Córdoba", "rack": "R-12", "estado": "activo" },
    { "id": 5, "clave": "18", "nombre": "Suc. 18 Orizaba", "ciudad": "Orizaba", "rack": "R-18", "estado": "activo" },
    { "id": 6, "clave": "21", "nombre": "Suc. 21 Tuxpan", "ciudad": "Tuxpan", "rack": "R-21", "estado": "activo" }
  ],
  "total": 6
}
```

**`POST /api/sucursales`**

```json
{ "clave": "09", "nombre": "Suc. 09 Veracruz Puerto", "ciudad": "Veracruz" }
```

**201**

```json
{ "id": 7, "clave": "09", "nombre": "Suc. 09 Veracruz Puerto", "ciudad": "Veracruz", "rack": "R-09", "estado": "activo" }
```

**Errores**

| HTTP | `code` | `detail` | Cuándo |
|---|---|---|---|
| 409 | `clave_duplicada` | Esta clave ya está registrada | Otra sucursal tiene la clave |
| 409 | `rack_ocupado` | Ese rack ya está asignado | El rack `R-<clave>` ya tiene sucursal |
| 422 | `validacion` | Completa Clave · Completa Sucursal · Completa Ciudad | Falta un campo obligatorio |
| 422 | `validacion` | La clave debe ser de 01 a 32 | Clave fuera de rango o con otro formato |
| 422 | `validacion` | La clave no se puede cambiar | `PATCH` con `clave` o `rack` |

### Usuarios · `/api/usuarios`

Columnas de Oficina: Usuario, Nombre, Rol, Canal, Estado.

| Campo | Tipo | Al crear | Reglas |
|---|---|---|---|
| `id` | entero | — | Solo lectura |
| `usuario` | cadena | Obligatorio | Se guarda en minúsculas. Letras, números, punto, guion y guion bajo, de 3 a 40. Único |
| `nombre` | cadena | Obligatorio | Hasta 120 caracteres |
| `rol` | cadena | Obligatorio | De la lista de [Roles](#roles) |
| `canal` | cadena | — | Solo lectura. Lo define el rol |
| `sucursal_id` | entero o `null` | Obligatorio si `rol` es `sucursal` | Debe existir. `null` para los demás roles |
| `proveedor_id` | entero o `null` | Obligatorio si `rol` es `proveedor` | Debe existir. `null` para los demás roles |
| `sucursal` · `proveedor` | objeto o `null` | — | Solo lectura: `{ id, nombre }` |
| `contrasena_temporal` | booleano | — | Solo lectura. `true` hasta que el usuario cambia su contraseña |
| `estado` | cadena | Opcional, `activo` | `activo` o `inactivo` |

- El usuario de un rol de Android empieza con su prefijo: `caseta.`, `desem.` o `embar.`. Un rol web no puede usar esos prefijos (R-01). La regla se revisa también al editar el usuario o el rol.
- Nunca se envía ni se devuelve la contraseña guardada. Oficina no captura contraseñas: el back genera una temporal (R-17).
- `?q=` busca en usuario y nombre.

**`GET /api/usuarios` · 200**

```json
{
  "items": [
    { "id": 1, "usuario": "caseta.jlopez", "nombre": "Jorge López", "rol": "caseta", "canal": "android", "sucursal_id": null, "sucursal": null, "proveedor_id": null, "proveedor": null, "contrasena_temporal": false, "estado": "activo" },
    { "id": 2, "usuario": "desem.mruiz", "nombre": "María Ruiz", "rol": "desembarque", "canal": "android", "sucursal_id": null, "sucursal": null, "proveedor_id": null, "proveedor": null, "contrasena_temporal": false, "estado": "activo" },
    { "id": 3, "usuario": "embar.acruz", "nombre": "Alan Cruz", "rol": "embarque", "canal": "android", "sucursal_id": null, "sucursal": null, "proveedor_id": null, "proveedor": null, "contrasena_temporal": false, "estado": "activo" },
    { "id": 4, "usuario": "suc07", "nombre": "Suc. 07 Boca del Río", "rol": "sucursal", "canal": "web", "sucursal_id": 3, "sucursal": { "id": 3, "nombre": "Suc. 07 Boca del Río" }, "proveedor_id": null, "proveedor": null, "contrasena_temporal": false, "estado": "activo" },
    { "id": 5, "usuario": "pgolfo", "nombre": "Papelera del Golfo", "rol": "proveedor", "canal": "web", "sucursal_id": null, "sucursal": null, "proveedor_id": 1, "proveedor": { "id": 1, "nombre": "Papelera del Golfo" }, "contrasena_temporal": false, "estado": "activo" },
    { "id": 6, "usuario": "admin.cedis", "nombre": "Ana Domínguez", "rol": "oficina", "canal": "web", "sucursal_id": null, "sucursal": null, "proveedor_id": null, "proveedor": null, "contrasena_temporal": false, "estado": "activo" }
  ],
  "total": 6
}
```

`admin.cedis` no aparece en la tabla de usuarios del prototipo, pero sí en LoginWeb y en el pie de la barra lateral de Oficina («Ana Domínguez · Oficina · Admin»). Se incluye para que Oficina pueda entrar.

**`POST /api/usuarios`**

```json
{ "usuario": "caseta.rgomez", "nombre": "Rosa Gómez", "rol": "caseta" }
```

**201**

```json
{
  "id": 7,
  "usuario": "caseta.rgomez",
  "nombre": "Rosa Gómez",
  "rol": "caseta",
  "canal": "android",
  "sucursal_id": null,
  "sucursal": null,
  "proveedor_id": null,
  "proveedor": null,
  "contrasena_temporal": true,
  "estado": "activo",
  "contrasena_generada": "Tmp-7Kq2-xW9p"
}
```

`contrasena_generada` solo viene en esta respuesta y en la de restablecer. El front se la muestra a Oficina una sola vez para que la entregue al usuario.

### `POST /api/usuarios/{id}/restablecer`

Oficina. Sin cuerpo. Genera una contraseña temporal nueva y deja `contrasena_temporal` en `true` (R-17). La anterior deja de servir.

**200:** el usuario con `contrasena_generada`, igual que al crear.

**Errores de usuarios**

| HTTP | `code` | `detail` | Cuándo |
|---|---|---|---|
| 409 | `usuario_duplicado` | Este usuario ya está registrado | Otro usuario tiene el mismo nombre de usuario |
| 409 | `no_puedes_eliminarte` | No puedes eliminar tu propio usuario | Oficina intenta borrar o desactivar su propio usuario |
| 422 | `validacion` | Completa Usuario · Completa Nombre · Completa Rol | Falta un campo obligatorio |
| 422 | `validacion` | El rol no es válido | `rol` fuera de la lista |
| 422 | `validacion` | El usuario de Caseta debe empezar con caseta. | Falta el prefijo del rol de Android (igual para `desem.` y `embar.`) |
| 422 | `validacion` | Ese prefijo es solo para usuarios de Android | Un rol web usa `caseta.`, `desem.` o `embar.` |
| 422 | `validacion` | Elige la sucursal · Elige el proveedor | Falta el vínculo del rol `sucursal` o `proveedor`, o no existe |

---

## Fuera de este contrato

- Los KPIs y la ocupación de racks de Oficina se calculan en el sprint 4 (BE-44, H-13). Mientras tanto, el front usa los valores del prototipo.
- La solicitud de recuperación de contraseña («¿Olvidaste tu contraseña?») es del sprint 5 (BE-50).
- La campana de avisos es del sprint 5 (BE-51).
- «Recordarme» no cambia la duración del token en el sprint 1.

## Preguntas abiertas

Se aplica el criterio por defecto mientras no haya respuesta. Si cambia, se actualiza este contrato y se avisa con un issue.

| # | Pregunta | Criterio por defecto |
|---|---|---|
| C1-01 | El formulario de Productos en Oficina no tiene proveedor principal, unidad ni ilustración (A-16 dice «sin agregar pantallas»). ¿Cómo los captura Oficina? | Son opcionales en la API. Las semillas los traen y Oficina no los edita en el sprint 1. |
| C1-02 | ¿Qué proveedor surte cada producto de las semillas? | RES y PAP de Papelera del Golfo; CUA y FOL de Grupo Escolar MX; ENG, LAP y CLI de Distribuidora Atlas. Útiles del Sureste queda sin productos porque está suspendido. |
| C1-03 | LoginWeb pide «Correo o usuario». ¿Se entra con correo? | Solo con usuario. Los usuarios no tienen correo en el catálogo. |
| C1-04 | El formulario de Usuarios no tiene campo para elegir la sucursal o el proveedor del usuario. | La API los pide para esos roles. El front necesita un selector; Ximena define cómo se ve con los componentes del prototipo. |
