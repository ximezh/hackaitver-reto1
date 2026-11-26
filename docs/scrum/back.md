# Plan Scrum · Back

**Responsable:** Jesus Vazquez y su agente
**Abarca:** APIs, endpoints, controladores, modelos, migraciones e instancia de PostgreSQL en Podman
**IDs:** `BE-NN` · **Épicas:** `BE-E1…` · **Ramas:** `back-<tipo>/sprint<N>` · **Commits:** `tipo(back): …`

Reglas generales, hallazgos, preguntas, DoR y DoD: [docs/scrum.md](../scrum.md).

## Reglas de esta área

- Las reglas de negocio (R-01…R-15 en `docs/scrum.md`) se aplican en el back y tienen pruebas.
- **Contrato primero:** el contrato del siguiente sprint se publica en `docs/api/sprint-<N>.md` durante el sprint actual. Si cambia después, se avisa a front y DevOps con un issue.
- Las pruebas corren contra una base de PostgreSQL de pruebas (`TEST_DATABASE_URL`), nunca contra la de desarrollo.
- Los textos de error que ve el usuario son los del prototipo («Ese andén ya está ocupado», «Este folio ya está registrado», etc.).
- Archivos propios: `back/`, `compose.yaml` y `docs/api/`. La configuración de CORS se lee de `CORS_ORIGINS`; DevOps define su valor por entorno.

## Épicas

| Épica | Nombre | Historias |
|---|---|---|
| BE-E1 | Base de datos y convenciones | BE-01…05 |
| BE-E2 | Acceso y catálogos | BE-10…16 |
| BE-E3 | Pedido, cita y factura | BE-20…25 |
| BE-E4 | Caseta y recepción | BE-30…35 |
| BE-E5 | Tarima, embarque e indicadores | BE-40…45 |
| BE-E6 | Complementos | BE-50…53 |

---

## Sprint 0 · Base de datos y convenciones

**Objetivo:** base en Podman con el esquema de catálogos, semillas del prototipo y el contrato del sprint 1.
**Rama:** `back-chore/sprint0` · **Puntos:** 16

### BE-01 · PostgreSQL en Podman para desarrollo y pruebas · 3 pts
Como desarrollador quiero levantar la base con un comando para trabajar y probar con PostgreSQL real.
- `podman compose up -d` levanta PostgreSQL 17 con las bases `reto1` y `reto1_test`.
- `TEST_DATABASE_URL` en `.env.example`; las pruebas fallan con un mensaje claro si falta o si es igual a `DATABASE_URL`.
- `conftest.py` deja la base de pruebas con la última migración antes de las pruebas.
- El README explica cómo usarlo con Podman y con Docker.

### BE-02 · Esquema de catálogos · 5 pts
Como desarrollador quiero los modelos de catálogos con sus restricciones para que los datos no se dupliquen.
- Modelos `Producto` (SKU, nombre, ilustración, unidad, piezas por bulto, kg, m³, proveedor principal), `Proveedor` (RFC, nombre, contacto, teléfono, estado), `Sucursal` (clave, nombre, ciudad, rack, estado), `Usuario` (usuario, nombre, rol, canal, contraseña, contraseña temporal, estado, sucursal o proveedor), `Anden` (R1–R4, E1–E3) y `Rack` (32).
- SKU, RFC, clave de sucursal y usuario son únicos.
- Migración de Alembic con pruebas de las restricciones.

### BE-03 · Semillas del prototipo · 3 pts
Como equipo queremos datos de ejemplo iguales al prototipo para que las demos se vean como el diseño.
- Comando `uv run python -m app.seeds` que carga los 7 productos, 4 proveedores, 6 sucursales y 5 usuarios de `bundle.js` y `Oficina/preview.html`, los 7 andenes y los 32 racks.
- Es idempotente: correrlo dos veces no duplica datos.
- No corre en producción sin una bandera explícita.

### BE-04 · Convenciones de la API · 3 pts
Como consumidor de la API quiero respuestas y errores uniformes para manejarlos igual en todas las pantallas.
- Errores con forma `{ "detail": "...", "code": "..." }` y códigos HTTP consistentes.
- Generador de folios con prefijo (`OC-26-`, `FAC-`, `B-`, `T-<suc>-`, `EMB-`) respaldado por secuencias de PostgreSQL (R-12).
- Fechas en `America/Mexico_City`.
- Pruebas de errores y folios.

### BE-05 · Contrato del sprint 1 · 2 pts
Como front y DevOps queremos el contrato del sprint 1 antes de empezarlo para trabajar con mocks.
- `docs/api/sprint-1.md` con login, sesión y CRUD de los cuatro catálogos: rutas, cuerpos, respuestas y errores.
- Ejemplos de respuesta con datos del prototipo.

---

## Sprint 1 · Acceso y catálogos

**Objetivo:** login por rol y CRUD de catálogos para Oficina.
**Rama:** `back-feat/sprint1` · **Puntos:** 24

### BE-10 · Autenticación por rol · 5 pts
Como usuario quiero iniciar sesión y que el sistema sepa mi rol para ver solo lo mío.
- `POST /api/auth/login` y `GET /api/auth/me`; JWT con rol y canal; contraseñas con Argon2 (A-09).
- Un rol de Android no entra por la web ni al revés.
- Usuarios inactivos no pueden entrar.
- Dependencia `requiere_rol(...)` para proteger cada endpoint.

### BE-11 · Productos · 3 pts
Como oficina quiero administrar productos para que el catálogo esté al día.
- CRUD en `/api/productos` con búsqueda.
- Peso, volumen y piezas mayores a cero.
- Un producto con historial se desactiva en lugar de borrarse (H-11).

### BE-12 · Proveedores · 3 pts
Como oficina quiero administrar proveedores y suspenderlos cuando haga falta.
- CRUD en `/api/proveedores` con estado Activo o Suspendido.
- RFC con formato válido y único.
- Un proveedor suspendido no puede agendar citas.

### BE-13 · Sucursales · 3 pts
Como oficina quiero administrar sucursales con su rack.
- CRUD en `/api/sucursales`; el rack `R-<clave>` se asigna al crear (R-15).
- No se asignan dos sucursales al mismo rack.

### BE-14 · Usuarios · 5 pts
Como oficina quiero dar de alta usuarios con su rol para controlar el acceso.
- CRUD en `/api/usuarios`; el rol se elige de la lista fija y define el canal.
- Los roles de Android exigen el prefijo `caseta.`, `desem.` o `embar.` (R-01).
- Sucursal y proveedor se vinculan a su registro.
- Al crear o restablecer un usuario, el back genera una contraseña temporal que se muestra una sola vez (R-17).

### BE-15 · Contraseña temporal y perfil · 3 pts
Como usuario nuevo quiero cambiar mi contraseña temporal en el primer inicio de sesión para que solo yo la conozca.
- El login indica si la contraseña es temporal; mientras lo sea, solo se permite `GET /api/auth/me` y `POST /api/auth/contrasena` (R-17).
- `POST /api/auth/contrasena` pide la actual y la nueva, con longitud mínima.
- `GET /api/auth/me` devuelve el perfil: nombre, usuario y rol.

### BE-16 · Contrato del sprint 2 · 2 pts
- `docs/api/sprint-2.md` con pedidos, OC, citas, disponibilidad, facturas, bultos y etiquetas.

---

## Sprint 2 · Pedido, cita y factura

**Objetivo:** la sucursal pide, el proveedor agenda sin empalmes y captura su factura por bulto.
**Rama:** `back-feat/sprint2` · **Puntos:** 28

### BE-20 · Pedido de sucursal y OC · 5 pts
Como sucursal quiero enviar mi pedido por bultos para que el CEDIS genere la orden de compra.
- `POST /api/pedidos` con líneas SKU y bultos; genera una OC cuyas líneas llevan producto y proveedor principal del producto (R-16, A-16).
- Relación muchos a muchos entre OC y proveedor a través de las líneas.
- `GET /api/pedidos` de la sucursal con el paso actual de los 6 (R-14) y la fecha estimada.

### BE-21 · Orden de requerimiento al proveedor · 3 pts
Como proveedor quiero ver las OC que me tocan con su destino y número de bultos.
- `GET /api/proveedor/ordenes` con OC, sucursal destino y los bultos de **su parte** de la OC, solo del proveedor de la sesión.
- Cada proveedor agenda, factura y entrega su parte por separado.
- La OC pasa al paso «Proveedor».

### BE-22 · Citas por andén · 8 pts
Como proveedor quiero agendar una cita en un andén y horario libres para entregar sin esperar.
- `GET /api/citas/disponibilidad?dia=` con bloques ocupados por andén.
- `POST /api/citas` aplica R-02, R-03 y R-04: citas de lunes a sábado, hasta 2 semanas adelante; se puede agendar a cualquier hora.
- El folio se rechaza si ya está registrado para alguno de los productos de esa parte de la OC.
- El empalme se impide con una restricción `EXCLUDE` en PostgreSQL (A-08), con prueba de dos citas simultáneas.
- Errores con los textos del prototipo.

### BE-23 · Factura desglosada por bulto · 5 pts
Como proveedor quiero capturar mi factura por bulto para que cada bulto tenga su etiqueta.
- Factura ligada a la parte del proveedor en la OC; bultos con folio `B-`, un solo SKU (R-05), piezas, peso y volumen.
- Restricción única en PostgreSQL sobre folio y producto (R-04).
- Totales de bultos, peso y volumen; avisa si los bultos no cuadran con la OC.

### BE-24 · Etiquetas QR en PDF · 5 pts
Como proveedor quiero descargar las etiquetas en PDF para imprimirlas y pegarlas.
- `GET /api/facturas/{folio}/etiquetas.pdf` (todas) y `GET /api/bultos/{folio}/etiqueta.pdf`.
- QR real con bulto, OC, sucursal, SKU y piezas (R-06, A-10); diseño de la etiqueta igual a la vista del prototipo.

### BE-25 · Contrato del sprint 3 · 2 pts
- `docs/api/sprint-3.md` con caseta, check-in, check-out, recepción, incidencias y bulto.

---

## Sprint 3 · Caseta y recepción

**Objetivo:** registrar la llegada del camión y recibir bultos contra la OC.
**Rama:** `back-feat/sprint3` · **Puntos:** 25

### BE-30 · Citas y salidas del día para caseta · 5 pts
Como caseta quiero ver las citas y salidas del día con su estado para saber qué camión atender.
- `GET /api/caseta/hoy` con entradas y salidas, estado (espera, dentro, salió), minutos de retraso y andenes ocupados.
- KPIs Dentro, Por llegar y Salieron.

### BE-31 · Check-in y check-out · 5 pts
Como caseta quiero registrar entrada y salida del camión con placa, operador y sello.
- Check-in por QR de la cita o placa; ocupa el andén. Check-out lo libera (R-13).
- No se registra dos veces la misma entrada.

### BE-32 · Recepción por escaneo · 8 pts
Como supervisor de desembarque quiero escanear un bulto y saber si se recibe.
- `POST /api/recepciones/{oc}/escaneos` responde recibido (con su caja por peso), excedente o SKU no solicitado (R-07, R-08).
- Avance: recibidos, faltantes y rechazados.
- Cerrar recepción deja la OC en el paso «En CEDIS».

### BE-33 · Reporte de incidencias · 3 pts
Como supervisor quiero reportar al proveedor lo que no se recibe.
- Registra la incidencia con bulto, motivo y hora; aparece en el historial del proveedor.

### BE-34 · Detalle de bulto · 2 pts
- `GET /api/bultos/{folio}` con producto, factura, OC, proveedor, sucursal, caja de tarima y los bultos de la misma factura.

### BE-35 · Contrato del sprint 4 · 2 pts
- `docs/api/sprint-4.md` con tarimas, embarques, relación, recepción en sucursal, historiales e indicadores.

---

## Sprint 4 · Tarima, embarque e indicadores

**Objetivo:** armar tarimas, embarcar al 90 %, generar la relación y calcular indicadores reales.
**Rama:** `back-feat/sprint4` · **Puntos:** 30

### BE-40 · Tarimas por sucursal · 8 pts
Como supervisor quiero que cada bulto vaya a su tarima y caja para no exceder la capacidad.
- Tarima `T-<suc>-<n>` por sucursal; el bulto escaneado se asigna a su caja por peso (R-08).
- Rechaza el bulto si excede 1,000 kg, 2.576 m³ o 2.00 m de altura (R-09).
- La tarima se cierra con cualquier porcentaje y se ubica en el rack de la sucursal (R-15).

### BE-41 · Embarques en tortón · 8 pts
Como supervisor de embarque quiero cargar y verificar tarimas hasta llegar al 90 %.
- Embarque `EMB-` por sucursal, con andén E y placa; hasta 12 tarimas.
- Verificar confirma que la tarima es la almacenada.
- Capacidad de 12,000 kg y 30.91 m³. Listo para salir cuando el volumen llega al 90 % (27.82 m³) o, si no, el peso llega al 90 % (10,800 kg) (R-10).
- Rechaza cargar una tarima que haga pasar el peso de 12,000 kg.
- Pruebas de los dos caminos de la regla y del tope.

### BE-42 · Relación de embarque en PDF · 5 pts
- `GET /api/embarques/{folio}/relacion.pdf` con QR, sucursal, placa y **todas** las tarimas (H-15).

### BE-43 · Recepción en sucursal · 2 pts
- `POST /api/pedidos/recibir` con el QR de la relación; deja el pedido en «Recibido».

### BE-44 · Historiales e indicadores · 5 pts
Como oficina, sucursal y proveedor queremos indicadores calculados con datos reales (H-13).
- Oficina: camiones recibidos hoy / citas del día, embarques hoy / programados, % de recepciones sin error, ocupación de los 32 racks.
- Proveedor: entregas del mes, % a tiempo, con incidencia, descarga promedio, e historial.
- Sucursal: bultos recibidos del mes, % completos, tiempo OC → entrega, faltantes, e historial.

### BE-45 · Contrato del sprint 5 · 2 pts
- `docs/api/sprint-5.md` con recuperación de contraseña, avisos, búsqueda y datos de las pestañas móviles.

---

## Sprint 5 · Complementos

**Objetivo:** recuperación de contraseña, avisos, búsqueda y datos de las pestañas móviles.
**Rama:** `back-feat/sprint5` · **Puntos:** 16

### BE-50 · Recuperación de contraseña por Oficina · 3 pts
Como usuario quiero pedir una contraseña nueva cuando olvido la mía.
- `POST /api/auth/recuperacion` registra la solicitud y crea un aviso para Oficina; responde igual exista o no el usuario.
- Oficina restablece la contraseña desde Usuarios con una temporal nueva (R-17).

### BE-51 · Avisos · 5 pts
Como usuario quiero recibir avisos de lo que pasa con mis entregas, pedidos y andenes.
- `GET /api/avisos` con no leídos primero y `POST /api/avisos/{id}/leido`.
- Avisos por rol: proveedor (cita confirmada, bulto rechazado), sucursal (cambio de paso del pedido), caseta (camión con retraso), desembarque (camión en andén), embarque (tortón listo para salir), oficina (solicitud de contraseña, incidencia de recepción).

### BE-52 · Búsqueda · 3 pts
- `GET /api/buscar?q=` devuelve, según el rol, productos y pedidos (sucursal) u OC y facturas (proveedor).

### BE-53 · Datos de las pestañas móviles · 5 pts
- Caseta: citas por día y andén, historial de entradas y salidas.
- Desembarque: OC por recibir hoy, tarimas armando y cerradas, historial de recepciones.
- Embarque: embarques por cargar hoy, tarimas listas, historial de embarques.

---

## Backlog de back

| ID | Historia | Origen |
|---|---|---|
| — | Sin historias todavía | — |

## Avance

| Sprint | Estado | PR |
|---|---|---|
| 0 | Hecho | #6 |
| 1 | Hecho | #12 |
| 2 | En revisión | #22 |
| 3 | Pendiente | — |
| 4 | Pendiente | — |
| 5 | Pendiente | — |
