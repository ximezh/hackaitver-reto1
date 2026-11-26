# Contrato del sprint 2 · Pedido, cita y factura

Historias que lo implementan: BE-20 a BE-24. Convenciones de rutas, errores, fechas, listas y folios: [README.md](README.md). Los ejemplos usan los datos del prototipo (`Sucursal/preview.html`, `Proveedor/preview.html` y `Bulto/preview.html`) y las semillas.

| Ruta | Rol | Historia |
|---|---|---|
| `GET /api/productos` | Oficina, **Sucursal** (solo activos) | BE-20 |
| `POST /api/pedidos` · `GET /api/pedidos` · `GET /api/pedidos/{folio}` | Sucursal | BE-20 |
| `GET /api/proveedor/ordenes` | Proveedor | BE-21 |
| `GET /api/citas/disponibilidad?dia=` | Proveedor | BE-22 |
| `GET /api/facturas/verificar?folio=&oc=` | Proveedor | BE-22 |
| `POST /api/citas` | Proveedor | BE-22 |
| `GET /api/facturas` · `GET /api/facturas/{folio}` | Proveedor | BE-23 |
| `POST /api/facturas/{folio}/bultos` · `DELETE /api/bultos/{folio}` | Proveedor | BE-23 |
| `GET /api/bultos/{folio}/qr.svg` | Proveedor, Oficina | BE-24 |
| `GET /api/bultos/{folio}/etiqueta.pdf` · `GET /api/facturas/{folio}/etiquetas.pdf` | Proveedor, Oficina | BE-24 |

Un proveedor solo ve y modifica **su parte** de cada OC (R-16). Si pide una OC, factura o bulto que no es suyo, la respuesta es `404 no_encontrado`, igual que si no existiera.

---

## Valores fijos

### Pasos del pedido (R-14)

| `paso` | `paso_indice` | Etiqueta | Cuándo empieza |
|---|---|---|---|
| `oc_emitida` | 0 | OC emitida | Al crear el pedido |
| `proveedor` | 1 | Proveedor | Cuando el primer proveedor confirma su cita (sprint 2) |
| `en_cedis` | 2 | En CEDIS | Cuando se cierra la recepción de todas las partes (sprint 3) |
| `en_tarima` | 3 | En tarima | Cuando sus bultos están en tarima (sprint 4) |
| `en_camino` | 4 | En camino | Cuando sale el embarque (sprint 4) |
| `recibido` | 5 | Recibido | Cuando la sucursal recibe con el QR (sprint 4) |

El front pinta los pasos `< paso_indice` como hechos, el igual como actual y los demás pendientes.

### Andenes de recibo y horario (R-02, R-13)

- Andenes de recibo: `R1`, `R2`, `R3`, `R4`.
- Horario: de `08:00` a `18:00`, en bloques de 30 minutos: 20 bloques por andén y día.
- Duración: `60`, `90`, `120` o `180` minutos (1, 1.5, 2 y 3 h). La cita termina a más tardar a las 18:00.
- Días: de lunes a sábado, desde hoy hasta 14 días después (2 semanas). El proveedor agenda a cualquier hora, cualquier día.
- Las horas son de `America/Mexico_City`, en formato `HH:MM`.

### Estados de la cita

| `estado` | Etiqueta | Chip |
|---|---|---|
| `programada` | Programada | `mute` |

Los estados de llegada, descarga y salida llegan en el sprint 3.

---

## Pedidos de sucursal (BE-20)

### `GET /api/productos` para Sucursal

Misma ruta y forma que en el sprint 1. Con el rol `sucursal` responde solo los productos `activo` y acepta `?q=`. Sucursal no puede crear, editar ni borrar (`403 sin_permiso`).

### `POST /api/pedidos`

Sucursal. La sucursal sale de la sesión.

```json
{ "lineas": [ { "sku": "PAP-0100", "bultos": 4 }, { "sku": "LAP-0012", "bultos": 2 } ] }
```

- Si un SKU se repite, se suman sus bultos.
- Cada línea toma el **proveedor principal** del producto (A-16). Las líneas de un mismo proveedor forman su **parte** de la OC (R-16).

**201**

```json
{
  "folio": "OC-26-1211",
  "creado_en": "2026-11-25T10:12:00-06:00",
  "sucursal": { "id": 3, "clave": "07", "nombre": "Suc. 07 Boca del Río" },
  "paso": "oc_emitida",
  "paso_indice": 0,
  "llega_estimado": "2026-11-28",
  "embarque": null,
  "bultos": 6,
  "kg": 25.2,
  "m3": 0.088,
  "lineas": [
    {
      "producto": { "id": 5, "sku": "PAP-0100", "nombre": "Hojas carta, paquete 100", "ilustracion": "hojas", "unidad": "paquetes", "piezas_por_bulto": 10 },
      "proveedor": { "id": 1, "nombre": "Papelera del Golfo" },
      "bultos": 4,
      "piezas": 40,
      "kg": 20.4,
      "m3": 0.072
    },
    {
      "producto": { "id": 6, "sku": "LAP-0012", "nombre": "Lápiz HB, caja 12", "ilustracion": "lapices", "unidad": "cajas", "piezas_por_bulto": 24 },
      "proveedor": { "id": 2, "nombre": "Distribuidora Atlas" },
      "bultos": 2,
      "piezas": 48,
      "kg": 4.8,
      "m3": 0.016
    }
  ],
  "partes": [
    { "proveedor": { "id": 1, "nombre": "Papelera del Golfo" }, "bultos": 4, "cita": null },
    { "proveedor": { "id": 2, "nombre": "Distribuidora Atlas" }, "bultos": 2, "cita": null }
  ]
}
```

- `kg` y `m3` son estimados: bultos × peso y volumen del bulto en el catálogo.
- `llega_estimado` (fecha) es una estimación (ver [Preguntas abiertas](#preguntas-abiertas)). El front lo muestra como «Llega Vie 28».
- `embarque` es `null` hasta el sprint 4; luego trae el folio `EMB-…`.
- `partes[].cita` es `null` o `{ "anden": "R1", "dia": "2026-11-26", "inicio": "08:00", "fin": "09:00" }`.
- El aviso del front es «`<folio>` enviada al CEDIS», como en el prototipo.

**Errores**

| HTTP | `code` | `detail` | Cuándo |
|---|---|---|---|
| 422 | `validacion` | Agrega productos | `lineas` vacío o ausente |
| 422 | `validacion` | Los bultos deben ser al menos 1 | `bultos` < 1 |
| 422 | `validacion` | Un pedido admite hasta 999 bultos por producto | `bultos` > 999 |
| 422 | `validacion` | El producto RES-0500 no está disponible | El SKU no existe o está inactivo |
| 422 | `validacion` | El producto RES-0500 no tiene proveedor asignado. Comunícate con Oficina | Sin proveedor principal |
| 422 | `validacion` | El proveedor de RES-0500 está suspendido. Comunícate con Oficina | Proveedor principal suspendido o inactivo |

En estos errores, `campos` usa la llave `lineas`.

### `GET /api/pedidos`

Sucursal: solo los suyos, del más nuevo al más antiguo. `?en_curso=true` deja fuera los `recibido` (vista «En camino» y su conteo en la navegación).

**200:** `{ "items": [ <pedido>, … ], "total": 3 }`, con la misma forma que la respuesta de `POST`.

### `GET /api/pedidos/{folio}`

Sucursal: un pedido suyo. Si no es suyo: `404 no_encontrado`.

---

## Orden de requerimiento al proveedor (BE-21)

### `GET /api/proveedor/ordenes`

Proveedor. Su parte de cada OC, de la más nueva a la más antigua. `?sin_cita=true` deja solo las que aún no tienen cita (el selector «Orden de compra» de «Agendar cita»).

**200**

```json
{
  "items": [
    {
      "oc": "OC-26-1182",
      "creado_en": "2026-11-21T09:40:00-06:00",
      "sucursal": { "id": 3, "clave": "07", "nombre": "Suc. 07 Boca del Río" },
      "bultos": 24,
      "kg": 321.4,
      "m3": 0.572,
      "lineas": [
        {
          "producto": { "id": 5, "sku": "PAP-0100", "nombre": "Hojas carta, paquete 100", "ilustracion": "hojas", "unidad": "paquetes", "piezas_por_bulto": 10, "kg": 5.1, "m3": 0.018 },
          "bultos": 14,
          "piezas": 140
        },
        {
          "producto": { "id": 1, "sku": "RES-0500", "nombre": "Resma carta 500 hojas", "ilustracion": "hojas", "unidad": "resmas", "piezas_por_bulto": 10, "kg": 25.0, "m3": 0.032 },
          "bultos": 10,
          "piezas": 100
        }
      ],
      "cita": null,
      "factura": null
    }
  ],
  "total": 1
}
```

- `bultos`, `kg`, `m3` y `lineas` son **solo los de este proveedor** (R-16).
- `lineas[].producto` incluye `kg` y `m3` del catálogo: el formulario «+ Bulto» los usa como valores iniciales (P-03).
- `cita`: `null` o la cita (ver `POST /api/citas`).
- `factura`: `null` o `{ "folio": "FAC-A-20418", "bultos_capturados": 6 }`.
- El selector muestra «`OC-26-1182 · Suc. 07 Boca del Río`», y el resumen muestra «Destino» y «Bultos», como el prototipo.

---

## Citas por andén (BE-22)

### `GET /api/citas/disponibilidad?dia=2026-11-26`

Proveedor. Bloques ocupados de un día en los 4 andenes de recibo.

**200**

```json
{
  "dia": "2026-11-26",
  "abre": "08:00",
  "cierra": "18:00",
  "bloque_min": 30,
  "andenes": [
    {
      "anden": "R1",
      "ocupados": [
        { "inicio": "08:00", "fin": "09:00", "etiqueta": "Distribuidora Atlas", "propia": false },
        { "inicio": "11:00", "fin": "12:00", "etiqueta": "OC-26-1182", "propia": true }
      ]
    },
    { "anden": "R2", "ocupados": [] },
    { "anden": "R3", "ocupados": [] },
    { "anden": "R4", "ocupados": [] }
  ]
}
```

- `etiqueta`: en las citas propias es el folio de la OC. En las de otros proveedores es el nombre del proveedor, como en el prototipo («Atlas», «Escolar MX»). Ver [Preguntas abiertas](#preguntas-abiertas).
- El calendario del prototipo muestra «Ocupado» en gris y «Tu cita» en azul. «Tu cita» es la selección local del front antes de confirmar.

**Errores de `dia`** (también aplican a `POST /api/citas`)

| HTTP | `code` | `detail` | Cuándo |
|---|---|---|---|
| 422 | `validacion` | Completa Día | Falta `dia` |
| 422 | `validacion` | Las citas son de lunes a sábado | `dia` es domingo |
| 422 | `validacion` | Ese día ya pasó | `dia` es anterior a hoy |
| 422 | `validacion` | Solo se agenda hasta 2 semanas adelante | `dia` es posterior a hoy + 14 días |

### `GET /api/facturas/verificar?folio=FAC-A-20418&oc=OC-26-1182`

Proveedor. Revisa el folio antes de confirmar, para marcarlo en rojo como el prototipo. La validación final la hace `POST /api/citas`.

**200**

```json
{ "folio": "FAC-A-20418", "disponible": true, "detail": null }
```

```json
{ "folio": "FAC-A-20391", "disponible": false, "detail": "Este folio ya está registrado" }
```

- El folio se compara en mayúsculas y sin espacios al inicio ni al final.
- Está **registrado** si ya existe con el mismo folio para **alguno de los productos** de la parte de esa OC, de cualquier proveedor (R-04, P-02). Una factura puede cubrir varios productos: el mismo folio para productos distintos sí se permite.
- Si `folio` está vacío: `{ "disponible": false, "detail": "El folio es obligatorio" }`.

### `POST /api/citas`

Proveedor.

```json
{
  "oc": "OC-26-1182",
  "folio_factura": "FAC-A-20418",
  "anden": "R1",
  "dia": "2026-11-26",
  "inicio": "11:00",
  "duracion_min": 60
}
```

**201**

```json
{
  "id": 41,
  "oc": "OC-26-1182",
  "sucursal": { "id": 3, "clave": "07", "nombre": "Suc. 07 Boca del Río" },
  "proveedor": { "id": 1, "nombre": "Papelera del Golfo" },
  "folio_factura": "FAC-A-20418",
  "anden": "R1",
  "dia": "2026-11-26",
  "inicio": "11:00",
  "fin": "12:00",
  "duracion_min": 60,
  "bultos": 24,
  "estado": "programada",
  "creado_en": "2026-11-25T10:20:00-06:00"
}
```

- Registra la factura `folio_factura` para los productos de la parte del proveedor (R-04). Desde aquí se capturan sus bultos (BE-23).
- La OC pasa al paso `proveedor` si estaba en `oc_emitida`.
- Una parte de OC tiene una sola cita. Reagendar y cancelar no están en el prototipo (ver [Preguntas abiertas](#preguntas-abiertas)).
- El aviso del front es «Cita confirmada · QR enviado», como el prototipo. El QR de la cita para la caseta se define en el contrato del sprint 3.

**Errores**

| HTTP | `code` | `detail` | Cuándo |
|---|---|---|---|
| 409 | `anden_ocupado` | Ese andén ya está ocupado | Se empalma con otra cita del mismo andén (R-03). Lo impide la restricción `EXCLUDE` aunque dos proveedores confirmen al mismo tiempo (A-08) |
| 409 | `folio_registrado` | Este folio ya está registrado | El folio ya existe para alguno de los productos de la parte (R-04) |
| 409 | `cita_existente` | Esta orden ya tiene cita | La parte de la OC ya tiene cita |
| 409 | `proveedor_suspendido` | Tu cuenta de proveedor está suspendida. Comunícate con Oficina | El proveedor no está `activo` (BE-12) |
| 404 | `no_encontrado` | No encontramos el registro | La OC no existe o no tiene parte de este proveedor |
| 422 | `validacion` | El folio es obligatorio | `folio_factura` vacío |
| 422 | `validacion` | El folio debe empezar con FAC- | Otro prefijo (R-12) |
| 422 | `validacion` | El folio admite hasta 30 caracteres | Folio largo |
| 422 | `validacion` | Elige un andén de recibo, de R1 a R4 | `anden` no es de recibo |
| 422 | `validacion` | Elige un horario de 8:00 a 18:00 en bloques de 30 minutos | `inicio` fuera del horario o sin bloque de 30 min |
| 422 | `validacion` | La cita debe terminar a más tardar a las 18:00 | `inicio` + `duracion_min` > 18:00 |
| 422 | `validacion` | Ese horario ya pasó | `dia` es hoy y `inicio` ya pasó |
| 422 | `validacion` | Elige una duración de 1, 1.5, 2 o 3 h | `duracion_min` fuera de la lista |
| 422 | `validacion` | Errores de `dia` | Ver la tabla de disponibilidad |

---

## Factura desglosada por bulto (BE-23)

### `GET /api/facturas`

Proveedor: sus facturas, de la más nueva a la más antigua. Cada elemento tiene la misma forma que `GET /api/facturas/{folio}`, sin `bultos`.

### `GET /api/facturas/{folio}`

Proveedor dueño de la factura.

**200**

```json
{
  "folio": "FAC-A-20418",
  "oc": "OC-26-1182",
  "sucursal": { "id": 3, "clave": "07", "nombre": "Suc. 07 Boca del Río" },
  "proveedor": { "id": 1, "nombre": "Papelera del Golfo" },
  "bultos_esperados": 24,
  "totales": { "bultos": 2, "kg": 30.1, "m3": 0.05 },
  "cuadra": false,
  "diferencias": [
    { "sku": "PAP-0100", "esperados": 14, "capturados": 1 },
    { "sku": "RES-0500", "esperados": 10, "capturados": 1 }
  ],
  "bultos": [
    {
      "folio": "B-0003",
      "producto": { "id": 5, "sku": "PAP-0100", "nombre": "Hojas carta, paquete 100", "ilustracion": "hojas", "unidad": "paquetes" },
      "piezas": 10,
      "kg": 5.1,
      "m3": 0.018,
      "caja": "verde",
      "qr": "CEDIS1;B=B-0003;OC=OC-26-1182;SUC=07;SKU=PAP-0100;PZ=10"
    },
    {
      "folio": "B-0004",
      "producto": { "id": 1, "sku": "RES-0500", "nombre": "Resma carta 500 hojas", "ilustracion": "hojas", "unidad": "resmas" },
      "piezas": 10,
      "kg": 25.0,
      "m3": 0.032,
      "caja": "roja",
      "qr": "CEDIS1;B=B-0004;OC=OC-26-1182;SUC=07;SKU=RES-0500;PZ=10"
    }
  ]
}
```

- KPIs del prototipo: «Factura» = `folio`, «Bultos» = «`totales.bultos` de `bultos_esperados`» (por ejemplo «6 de 24»), «Peso» = `totales.kg` y «Volumen» = `totales.m3`.
- `cuadra` es `true` cuando los bultos capturados por SKU son exactamente los de la OC. Si no, `diferencias` dice cuáles faltan o sobran. Es un aviso: no impide capturar ni imprimir.
- `caja` es la caja de tarima por peso del bulto (R-08): `roja` si pesa 15 kg o más, `naranja` desde 7 y hasta menos de 15 kg, `verde` si pesa menos de 7 kg.
- `qr` es el texto que codifica el QR de la etiqueta (R-06). Ver [QR de la etiqueta](#qr-de-la-etiqueta).

### `POST /api/facturas/{folio}/bultos`

Proveedor dueño. El formulario «+ Bulto» (P-03).

```json
{ "sku": "PAP-0100", "piezas": 10, "kg": 5.1, "m3": 0.018, "cantidad": 1 }
```

- `sku` debe ser uno de los productos de la parte del proveedor en esa OC. Un bulto lleva un solo producto (R-05).
- `piezas`, `kg` y `m3` son obligatorios. El front los propone con los valores del catálogo (`lineas[].producto` de `GET /api/proveedor/ordenes`).
- `cantidad` (opcional, por omisión 1, de 1 a 100) crea varios bultos iguales, cada uno con su folio `B-`.

**201**

```json
{
  "bultos": [
    {
      "folio": "B-0009",
      "producto": { "id": 5, "sku": "PAP-0100", "nombre": "Hojas carta, paquete 100", "ilustracion": "hojas", "unidad": "paquetes" },
      "piezas": 10,
      "kg": 5.1,
      "m3": 0.018,
      "caja": "verde",
      "qr": "CEDIS1;B=B-0009;OC=OC-26-1182;SUC=07;SKU=PAP-0100;PZ=10"
    }
  ],
  "factura": {
    "folio": "FAC-A-20418",
    "oc": "OC-26-1182",
    "sucursal": { "id": 3, "clave": "07", "nombre": "Suc. 07 Boca del Río" },
    "proveedor": { "id": 1, "nombre": "Papelera del Golfo" },
    "bultos_esperados": 24,
    "totales": { "bultos": 3, "kg": 35.2, "m3": 0.068 },
    "cuadra": false,
    "diferencias": [
      { "sku": "PAP-0100", "esperados": 14, "capturados": 2 },
      { "sku": "RES-0500", "esperados": 10, "capturados": 1 }
    ]
  }
}
```

`factura` tiene la misma forma que `GET /api/facturas/{folio}`, sin `bultos`, para actualizar los KPIs sin otra petición.

**Errores**

| HTTP | `code` | `detail` | Cuándo |
|---|---|---|---|
| 422 | `validacion` | Ese producto no está en la orden | El SKU no está en la parte del proveedor |
| 422 | `validacion` | Las piezas deben ser al menos 1 | `piezas` < 1 |
| 422 | `validacion` | El peso debe ser mayor a 0 | `kg` ≤ 0 |
| 422 | `validacion` | El peso no puede pasar de 1,000 kg, la capacidad de una tarima | `kg` > 1000 (R-09) |
| 422 | `validacion` | El volumen debe ser mayor a 0 | `m3` ≤ 0 |
| 422 | `validacion` | El volumen no puede pasar de 2.576 m³, la capacidad de una tarima | `m3` > 2.576 (R-09) |
| 422 | `validacion` | La cantidad debe ser de 1 a 100 bultos | `cantidad` fuera de rango |
| 409 | `folio_registrado` | Este folio ya está registrado | Restricción única de folio y producto en PostgreSQL (R-04) |

### `DELETE /api/bultos/{folio}`

Proveedor dueño. Quita un bulto capturado por error mientras no se haya recibido en el CEDIS.

**200:** `{ "resultado": "eliminado" }`. Si ya se recibió: `409 bulto_recibido` «Este bulto ya se recibió en el CEDIS» (sprint 3).

---

## Etiquetas QR (BE-24)

### QR de la etiqueta

El QR identifica bulto, OC, sucursal destino, SKU y piezas (R-06) con este texto:

```text
CEDIS1;B=B-0003;OC=OC-26-1182;SUC=07;SKU=PAP-0100;PZ=10
```

- `CEDIS1` es la versión del formato. Desembarque lo lee en el sprint 3.
- Los campos van separados por `;`, en este orden, sin espacios.

### `GET /api/bultos/{folio}/qr.svg`

Proveedor dueño u Oficina. El QR real en SVG para la «Vista de etiquetas» (`Content-Type: image/svg+xml`). Como pide el encabezado `Authorization`, el front lo descarga con Axios como `blob` y lo muestra con `URL.createObjectURL`.

### `GET /api/bultos/{folio}/etiqueta.pdf`

Proveedor dueño u Oficina. Una etiqueta en PDF (`Content-Type: application/pdf`, `Content-Disposition: attachment; filename="B-0003.pdf"`).

### `GET /api/facturas/{folio}/etiquetas.pdf`

Proveedor dueño u Oficina. Todas las etiquetas de la factura, varias por hoja carta para la impresora láser (`filename="FAC-A-20418-etiquetas.pdf"`).

- La etiqueta reproduce la vista del prototipo: QR a la izquierda y, a la derecha, «Bulto», «OC · Sucursal» y «SKU · Piezas».
- Factura sin bultos: `409 factura_sin_bultos` «Agrega bultos para imprimir sus etiquetas».

---

## Fuera de este contrato

- Recepción, caseta y el QR de la cita: sprint 3 (BE-25 publica su contrato).
- Historiales y KPIs de Proveedor y Sucursal: sprint 4 (BE-44). Mientras tanto, el front usa los valores del prototipo.
- Reagendar o cancelar una cita.

## Preguntas abiertas

Se aplica el criterio por defecto mientras no haya respuesta. Si cambia, se actualiza este contrato y se avisa en `AVISOS-front.md` y `AVISOS-devops.md`.

| # | Pregunta | Criterio por defecto |
|---|---|---|
| C2-01 | ¿Cuándo pasa la OC de «OC emitida» a «Proveedor»? | Cuando el primer proveedor de la OC confirma su cita. |
| C2-02 | ¿Cómo se calcula «Llega …» antes de que exista el embarque? | Al crear: 3 días hábiles (lunes a sábado) después de la fecha de la OC. Cuando todas las partes tienen cita: el siguiente día hábil después de la última cita. Desde el sprint 4, con la salida del embarque. |
| C2-03 | El calendario del prototipo muestra el nombre de los otros proveedores en los bloques ocupados. ¿Se muestra? | Sí, como el prototipo. Si no se quiere, se cambia la `etiqueta` a «Ocupado» sin cambiar la forma. |
| C2-04 | ¿Se puede reagendar o cancelar una cita? | No en el sprint 2: el prototipo no lo dibuja. Oficina lo resuelve a mano. |
| C2-05 | ¿Se acepta un pedido con productos de un proveedor suspendido? | No: el proveedor no podría agendar y el pedido quedaría detenido. |
