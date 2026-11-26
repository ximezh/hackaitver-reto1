# Contrato del sprint 3 · Caseta, recepción y bulto

Historias que lo implementan: BE-30 a BE-34. Convenciones: [README.md](README.md). Los ejemplos usan los datos de `Caseta/preview.html`, `Desembarque/preview.html` y `Bulto/preview.html`.

| Ruta | Rol | Historia |
|---|---|---|
| `GET /api/caseta/hoy` | Caseta | BE-30 |
| `POST /api/caseta/entradas` · `POST /api/caseta/salidas` | Caseta | BE-31 |
| `GET /api/citas/{id}/qr.svg` | Proveedor dueño, Caseta | BE-31 |
| `POST /api/recepciones/escaneos` · `POST /api/recepciones/{oc}/escaneos` | Sup. desembarque | BE-32 |
| `GET /api/recepciones/{oc}` · `POST /api/recepciones/{oc}/cerrar` | Sup. desembarque | BE-32 |
| `POST /api/incidencias` · `GET /api/incidencias` | Sup. desembarque (crear) · Proveedor y Oficina (listar) | BE-33 |
| `GET /api/bultos/{folio}` | Sup. desembarque, Sup. embarque, Oficina, Proveedor dueño | BE-34 |

---

## Valores fijos

### Estado de una entrada o salida en caseta

| `estado` | Chip en entradas | Chip en salidas | Acción |
|---|---|---|---|
| `espera` | «A tiempo» (`mute`) o «+N min» (`warn`) | «A tiempo» o «+N min» | Check-in |
| `dentro` | «Descargando» | «Cargando» | Check-out |
| `salio` | «Salió» (`ok`) | «Salió» (`ok`) | — |

`retraso_min` es `0` si el camión va a tiempo. En `espera`, son los minutos que lleva de retraso respecto a la hora de la cita; en `dentro` y `salio`, los que llegó tarde.

### Resultado de un escaneo en recepción (R-07, R-08)

| `resultado` | Se recibe | Pantalla del prototipo |
|---|---|---|
| `recibido` | Sí | «Bulto recibido» y el chip «A caja roja / naranja / verde» |
| `excedente` | No | «No se recibe» · chip «Excedente» |
| `no_solicitado` | No | «No se recibe» · chip «SKU no solicitado» |
| `otra_oc` | No | «No se recibe» · «Este bulto es de la OC-…» |
| `ya_recibido` | No (ya estaba) | Aviso «Este bulto ya se recibió» |

### QR que se escanean

| QR | Texto | Lo genera |
|---|---|---|
| Etiqueta del bulto | `CEDIS1;B=B-0003;OC=OC-26-1182;SUC=07;SKU=PAP-0100;PZ=10` | Sprint 2 (R-06) |
| Cita | `CEDIS1;C=41;OC=OC-26-1182` | Este sprint: `GET /api/citas/{id}/qr.svg` y campo `qr` de la cita |

Los endpoints que reciben un QR también aceptan el folio solo (`B-0003`) o el `id` de la cita, para capturarlo a mano si la cámara no lee.

---

## Caseta (BE-30, BE-31)

### `GET /api/caseta/hoy`

Caseta. Entradas (citas de recibo) y salidas (embarques) del día de la operación, en orden de hora.

**200**

```json
{
  "dia": "2026-11-25",
  "kpis": { "dentro": 3, "por_llegar": 3, "salieron": 2 },
  "andenes": [
    { "anden": "R1", "tipo": "recibo", "ocupado": false },
    { "anden": "R2", "tipo": "recibo", "ocupado": true },
    { "anden": "E1", "tipo": "embarque", "ocupado": true }
  ],
  "entradas": [
    {
      "cita_id": 41,
      "hora": "10:30",
      "proveedor": "Útiles del Sureste",
      "anden": "R4",
      "oc": "OC-26-1194",
      "duracion_min": 90,
      "placa": null,
      "estado": "espera",
      "retraso_min": 15
    }
  ],
  "salidas": [
    {
      "embarque": "EMB-0412",
      "hora": "10:15",
      "sucursal": "Suc. 07 Boca del Río",
      "anden": "E1",
      "placa": "TOR-551-V",
      "estado": "dentro",
      "retraso_min": 0
    }
  ]
}
```

- `andenes` lista los 7 andenes, R1 a R4 y E1 a E3. Un andén está ocupado mientras haya un camión `dentro` (R-13).
- `placa` es `null` hasta el check-in.
- `salidas` queda vacío hasta el sprint 4, cuando existen los embarques; la forma ya es la definitiva.
- La pantalla se actualiza consultando esta ruta cada 15 s (A-11).

### `POST /api/caseta/entradas`

Caseta. Check-in.

```json
{ "qr": "CEDIS1;C=41;OC=OC-26-1194", "placa": "MNX-204-D", "operador": "Raúl Méndez", "sello": "SL-77120" }
```

- `qr` es el QR de la cita. También acepta el `id` de la cita como texto (`"41"`), cuando se toca la fila en la lista.
- `placa`, `operador` y `sello` son obligatorios. La placa se guarda en mayúsculas.
- La cita pasa a `dentro`, se guarda la hora de llegada y el andén queda ocupado.
- El aviso del front es «Entrada `<placa>` · `<HH:MM>`», como el prototipo.

**200:** la entrada con la forma de `entradas[]`.

| HTTP | `code` | `detail` | Cuándo |
|---|---|---|---|
| 404 | `no_encontrado` | No encontramos la cita | El QR o `id` no corresponde a una cita |
| 409 | `entrada_registrada` | Esta entrada ya está registrada | La cita ya está `dentro` o `salio` |
| 409 | `cita_de_otro_dia` | Esta cita es para el `<día>` | La cita no es de hoy |
| 409 | `anden_ocupado` | El andén R2 sigue ocupado | Otro camión sigue `dentro` en ese andén |
| 422 | `validacion` | Completa Placa · Completa Operador · Completa Sello | Falta un dato |

### `POST /api/caseta/salidas`

Caseta. Check-out.

```json
{ "cita_id": 41 }
```

- También acepta `{ "placa": "MNX-204-D" }`, que busca el camión `dentro` con esa placa (el «o la placa del camión» del prototipo).
- La cita pasa a `salio`, se guarda la hora de salida y se libera el andén (R-13).
- Las salidas de tortones (`{ "embarque": "EMB-0412" }`) llegan en el sprint 4.
- El aviso del front es «Salida `<placa>` · `<HH:MM>`».

**200:** la entrada con la forma de `entradas[]`.

| HTTP | `code` | `detail` | Cuándo |
|---|---|---|---|
| 404 | `no_encontrado` | No hay un camión dentro con esa placa | Placa sin camión `dentro` |
| 409 | `sin_entrada` | Este camión no ha registrado su entrada | La cita sigue en `espera` |
| 409 | `salida_registrada` | Esta salida ya está registrada | La cita ya está `salio` |

### `GET /api/citas/{id}/qr.svg`

Proveedor dueño de la cita o Caseta. El QR de la cita en SVG, para mostrarlo en el portal del proveedor («Cita confirmada · QR enviado») y presentarlo en caseta. Como pide `Authorization`, se descarga como `blob`. `POST /api/citas` y `GET /api/proveedor/ordenes` agregan a la cita el campo `qr` con su texto.

---

## Recepción por escaneo (BE-32)

### `POST /api/recepciones/escaneos`

Sup. desembarque. Abre la OC escaneando su primer bulto (H-19) y responde igual que la ruta con `{oc}`.

```json
{ "qr": "CEDIS1;B=B-0003;OC=OC-26-1182;SUC=07;SKU=PAP-0100;PZ=10" }
```

### `POST /api/recepciones/{oc}/escaneos`

Sup. desembarque. Mismo cuerpo. Escanea un bulto contra la OC abierta.

**200 · recibido**

```json
{
  "resultado": "recibido",
  "detail": "Bulto recibido",
  "bulto": { "folio": "B-0003", "producto": { "sku": "PAP-0100", "nombre": "Hojas carta, paquete 100", "ilustracion": "hojas", "unidad": "paquetes" }, "piezas": 10, "kg": 5.1, "caja": "verde" },
  "recepcion": { "…": "misma forma que GET /api/recepciones/{oc}" }
}
```

**200 · rechazado**

```json
{
  "resultado": "excedente",
  "detail": "No se recibe",
  "bulto": { "folio": "B-0014", "producto": { "sku": "CLI-0100", "nombre": "Clip #1, caja 100", "ilustracion": "clips", "unidad": "cajas" }, "piezas": 40, "kg": 1.0, "caja": "verde" },
  "recepcion": { "…": "…" }
}
```

- Un escaneo rechazado (`excedente`, `no_solicitado`, `otra_oc`) suma uno a «Rechazados» y queda listo para «Reportar al proveedor» (BE-33).
- `ya_recibido` no cambia el avance.
- Un QR que no es de un bulto registrado responde `404 no_encontrado` «No encontramos ese bulto».
- Una recepción cerrada responde `409 recepcion_cerrada` «Esta recepción ya está cerrada».

### `GET /api/recepciones/{oc}`

Sup. desembarque. Avance de la recepción (anillo «x de N bultos», chips y líneas del prototipo).

**200**

```json
{
  "oc": "OC-26-1182",
  "sucursal": { "id": 3, "clave": "07", "nombre": "Suc. 07 Boca del Río" },
  "facturas": ["FAC-A-20418"],
  "pedidos": 24,
  "recibidos": 17,
  "faltan": 7,
  "rechazados": 1,
  "completa": false,
  "cerrada": false,
  "lineas": [
    { "producto": { "sku": "PAP-0100", "nombre": "Hojas carta, paquete 100", "ilustracion": "hojas", "kg": 5.1 }, "pide": 10, "recibidos": 8 }
  ]
}
```

### `POST /api/recepciones/{oc}/cerrar`

Sup. desembarque. Cierra la recepción, aunque falten bultos (los faltantes quedan registrados). La OC pasa al paso `en_cedis`.

**200:** la recepción con `cerrada: true`. El aviso del front es «Recepción cerrada · `<recibidos>` bultos», con el número real (H-04).

---

## Incidencias (BE-33)

### `POST /api/incidencias`

Sup. desembarque. «Reportar al proveedor».

```json
{ "oc": "OC-26-1182", "bulto": "B-0014", "motivo": "excedente", "nota": "" }
```

- `motivo`: `excedente`, `no_solicitado`, `otra_oc`, `faltante` o `danado`.
- `bulto` es opcional para `faltante`.
- Se guarda la hora del reporte. El aviso del front es «Reporte enviado».

**201**

```json
{ "id": 7, "oc": "OC-26-1182", "bulto": "B-0014", "proveedor": { "id": 1, "nombre": "Papelera del Golfo" }, "motivo": "excedente", "nota": null, "creado_en": "2026-11-25T11:42:00-06:00" }
```

### `GET /api/incidencias`

Proveedor: las suyas. Oficina: todas, con `?oc=`. Del más nuevo al más antiguo. Alimentan el historial del proveedor (BE-44).

---

## Detalle de bulto (BE-34)

### `GET /api/bultos/{folio}`

Sup. desembarque, Sup. embarque, Oficina y el proveedor dueño.

**200**

```json
{
  "folio": "B-0003",
  "estado": "en_anden",
  "producto": { "id": 5, "sku": "PAP-0100", "nombre": "Hojas carta, paquete 100", "ilustracion": "hojas", "unidad": "paquetes", "piezas_por_bulto": 10 },
  "piezas": 10,
  "kg": 5.1,
  "m3": 0.018,
  "caja": "verde",
  "oc": "OC-26-1182",
  "factura": "FAC-A-20418",
  "proveedor": { "id": 1, "nombre": "Papelera del Golfo" },
  "sucursal": { "id": 3, "clave": "07", "nombre": "Suc. 07 Boca del Río" },
  "qr": "CEDIS1;B=B-0003;OC=OC-26-1182;SUC=07;SKU=PAP-0100;PZ=10",
  "bultos_de_la_factura": [
    { "folio": "B-0003", "sku": "PAP-0100", "ilustracion": "hojas" },
    { "folio": "B-0004", "sku": "LAP-0012", "ilustracion": "lapices" }
  ]
}
```

| `estado` | Chip del prototipo |
|---|---|
| `por_llegar` | Por llegar |
| `en_anden` | En andén (su camión está `dentro`) |
| `recibido` | Recibido (`ok`) |
| `rechazado` | Rechazado (`bad`) |

- `bultos_de_la_factura` alimenta la tira de bultos y el carrusel, que pasa al siguiente bulto de la factura.
- La etiqueta en PDF sigue en `GET /api/bultos/{folio}/etiqueta.pdf` (sprint 2).

---

## Preguntas abiertas

| # | Pregunta | Criterio por defecto |
|---|---|---|
| C3-01 | La caseta del prototipo muestra la placa antes de que llegue el camión, pero la cita no la pide. ¿Quién la captura? | Caseta, en el check-in. Antes de llegar, la fila muestra «—». |
| C3-02 | ¿Se cierra una recepción con bultos faltantes? | Sí. Los faltantes quedan en la recepción y se pueden reportar con `motivo: faltante`. |
| C3-03 | ¿Cuántos minutos de tolerancia hay para «A tiempo»? | Ninguna: desde el minuto 1 de retraso se muestra «+N min». |
