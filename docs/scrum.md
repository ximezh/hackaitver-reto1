# Plan Scrum · CEDIS Flow

Plan general del producto. Cada área trabaja con su propio plan:

| Área | Responsable | Plan | Prefijo de IDs | Ramas |
|---|---|---|---|---|
| Front | Ximena Zaleta | [scrum/front.md](scrum/front.md) | `FE-` | `front-<tipo>/sprint<N>` |
| Back | Jesus Vazquez | [scrum/back.md](scrum/back.md) | `BE-` | `back-<tipo>/sprint<N>` |
| DevOps | Luis Daniel Morales | [scrum/devops.md](scrum/devops.md) | `DO-` | `devops-<tipo>/sprint<N>` |

Cada desarrollador trabaja con su agente sobre su propio archivo. Ninguna historia, rama o commit cruza a otra área; lo que una área necesita de otra se pide como se explica en [Coordinación entre áreas](#coordinación-entre-áreas).

---

## 1. Regla del prototipo

**El diseño del prototipo no se modifica.** La interfaz debe quedar idéntica a [`design/CEDIS Flow/`](../design/CEDIS%20Flow/): pantallas, textos, colores, tamaños, espacios, íconos, ilustraciones y animaciones.

- Solo se cambia algo del diseño cuando Ximena, Jesus o Luis Daniel lo indican de forma explícita. El cambio se anota en [Cambios de diseño autorizados](#cambios-de-diseño-autorizados) con quién lo pidió.
- `design/` es de solo lectura para todas las áreas y todos los agentes.
- Si el prototipo tiene un error o un hueco, no se corrige por cuenta propia: se anota en [Hallazgos](#7-hallazgos-del-prototipo) o en [Preguntas](#8-preguntas-y-respuestas-del-product-owner).
- Las **pantallas nuevas** autorizadas (perfil, contraseña, avisos, búsqueda, pestañas móviles) se construyen solo con los tokens, componentes, íconos e ilustraciones del prototipo. Ximena aprueba su diseño antes de programarlas.
- Los datos de ejemplo del prototipo (`components/bundle.js`) son referencia para semillas y mocks, no datos reales.

### Cambios de diseño autorizados

| Fecha | Cambio | Pantallas | Lo autorizó |
|---|---|---|---|
| 2026-11-25 | El canal Android es web responsiva: el layout móvil se adapta al ancho del dispositivo. No se dibujan el marco del teléfono ni la barra de estado «9:41». | Móviles | Luis Daniel |
| 2026-11-25 | El calendario de citas muestra de lunes a sábado. | Proveedor · Agendar cita | Luis Daniel |
| 2026-11-25 | «+ Bulto» abre un formulario con los mismos atributos del producto (producto, SKU, piezas, peso y volumen). | Proveedor · Factura y bultos | Luis Daniel |
| 2026-11-25 | Pantallas nuevas: perfil, cambio de contraseña obligatorio, recuperación de contraseña, panel de avisos, resultados de búsqueda y las pestañas inferiores de los roles móviles. | Todas | Luis Daniel |
| 2026-11-25 | Capacidades: tortón de 12,000 kg; tarima de 1.12 × 1.15 × 2.00 m (altura máxima 2.00 m en lugar de 1.85 m). Los números de las pantallas cambian en consecuencia. | Tarima3D, Embarque, Elementos | Luis Daniel |

---

## 2. Objetivo del producto

Digitalizar el flujo del CEDIS **de la orden de compra al embarque**: la sucursal pide, los proveedores agendan y entregan, el CEDIS recibe, arma tarimas y embarca, y la sucursal recibe. Cada trabajador ve solo las pantallas de su rol.

### Alcance

| Momento | Qué cubre | Pantallas |
|---|---|---|
| Previo | Pedido de la sucursal (OC) con productos de varios proveedores | Sucursal · Pedir |
| 1 · Agendamiento | Cita por andén, folio de factura, llegada a caseta | Proveedor · Agendar cita, Caseta |
| 2 · Identificación | Factura desglosada por bulto, etiqueta QR | Proveedor · Factura y bultos, Bulto |
| 3 · Recepción | Escaneo de bultos contra la OC, rechazos | Desembarque, Bulto |
| 4 · Almacenaje y embarque | Tarima por peso, tortón al 90 %, relación de embarque, salida y recepción en sucursal | Tarima3D, Embarque, Caseta, Sucursal · En camino |
| Transversal | Acceso por rol, catálogos, historiales e indicadores | LoginWeb, LoginMovil, Oficina, historiales |
| Complementos | Perfil, cambio y recuperación de contraseña, avisos, búsqueda y pestañas móviles | Pantallas nuevas (ver regla del prototipo) |

### Fuera de alcance

- App nativa o instalable: el canal Android es la web responsiva en el navegador del teléfono.
- Facturación electrónica (CFDI), timbrado o validación con el SAT. El folio de factura solo se captura.
- Integración con ERP, básculas o impresoras de etiquetas especiales. Se imprime con la impresora láser del navegador.
- Envío de correos: la recuperación de contraseña pasa por Oficina (ver P-10).
- Varios CEDIS: se opera un solo CEDIS (Veracruz).
- Los tableros de documentación del sistema de diseño (`Flujo`, `Cover`) no son pantallas del producto.

---

## 3. Supuestos por confirmar

| # | Supuesto | Criterio mientras tanto |
|---|---|---|
| S-01 | Duración de cada sprint y fechas | Sprints de 1 semana, sin fechas fijas. Se numeran del 0 al 5. |
| S-02 | Capacidad de cada desarrollador | Hasta ~28 puntos por área por sprint. Se ajusta al cerrar el sprint 1 con la velocidad real. |
| S-03 | Quién es el Product Owner | Ximena, Jesus y Luis Daniel deciden en conjunto. |
| S-04 | Usuarios de GitHub de cada integrante | Se necesitan para `CODEOWNERS` y revisiones (DO-02). |
| S-05 | Cuenta de AWS, región y dominio | Los aporta Luis Daniel antes de DO-12. |
| S-06 | Zona horaria de la operación | `America/Mexico_City` (CEDIS Veracruz). |

---

## 4. Sprint 0 · Configuración

**Objetivo:** que las tres áreas puedan trabajar en paralelo desde el sprint 1 sin pisarse.

| Entregable | Estado |
|---|---|
| Entornos de front (Vue 3 JS) y back (FastAPI + PostgreSQL) | Hecho · PR #1 |
| Prototipo versionado en `design/`, plan Scrum por área e instrucciones de agentes | Rama `devops-docs/sprint0` |
| Historias de sprint 0 de cada área | Ver `FE-01…`, `BE-01…`, `DO-01…` en cada plan |

---

## 5. Inventario del prototipo

### Roles y canales

| Rol | Canal | Usuario de ejemplo | Pantallas |
|---|---|---|---|
| Caseta | Android (web responsiva) | `caseta.jlopez` | LoginMovil → Caseta |
| Supervisor de desembarque | Android (web responsiva) | `desem.mruiz` | LoginMovil → Desembarque → Bulto → Tarima3D |
| Supervisor de embarque | Android (web responsiva) | `embar.acruz` | LoginMovil → Embarque → Tarima3D |
| Sucursal | Web | `suc07` | LoginWeb → Pedir, En camino, Historial |
| Proveedor | Web | `pgolfo` | LoginWeb → Agendar cita, Factura y bultos, Historial |
| Oficina | Web | `admin.cedis` | LoginWeb → Productos, Proveedores, Sucursales, Usuarios |

### Pantallas

| Componente | Archivo | Qué hace |
|---|---|---|
| Elementos | `components/Elementos/preview.html` | Botones, chips, campos, segmentado, barras y colores de tarima. |
| LoginMovil | `components/LoginMovil/preview.html` | Detecta el rol por prefijo del usuario, «Probar como», bienvenida con módulos. |
| LoginWeb | `components/LoginWeb/preview.html` | Pestañas Sucursal, Proveedor y Oficina con ilustración y lema. |
| Caseta | `components/Caseta/preview.html` | KPIs, 7 andenes, entradas y salidas, check-in (operador, sello) y check-out, escaneo de cita. |
| Desembarque | `components/Desembarque/preview.html` | Anillo de avance, escaneo contra OC, recibido, excedente o SKU no solicitado, reporte. |
| Bulto | `components/Bulto/preview.html` | Carrusel de 3 imágenes, tira de bultos de la factura, «Ver más» y etiqueta QR. |
| Tarima3D | `components/Tarima3D/preview.html` | Tarima en CSS 3D, giro, separar cajas, medidores, cajas por peso, escaneo. |
| Embarque | `components/Embarque/preview.html` | Tortón de 12 tarimas, regla del 90 %, verificar, relación de embarque. |
| Sucursal | `components/Sucursal/preview.html` | Pedir por bultos, seguimiento en 6 pasos, recibir con QR, historial. |
| Proveedor | `components/Proveedor/preview.html` | Calendario por andén, folio de factura, factura por bulto, etiquetas, historial. |
| Oficina | `components/Oficina/preview.html` | KPIs del día, ocupación de 32 racks, CRUD de 4 catálogos. |
| Flujo, Cover | `components/Flujo`, `components/Cover` | Documentación del sistema de diseño. No son pantallas. |

Recursos compartidos: `tokens.css` y `tokens.json` (colores, tipografía, espacios, radios y sombras), `components/bundle.css` (estilos de todos los componentes), `components/bundle.js` (íconos, catálogo de ejemplo, regla de zona) y 14 ilustraciones SVG en `assets/Ilustraciones/`.

### Reglas de negocio

| # | Regla | Origen | Quién la aplica |
|---|---|---|---|
| R-01 | El rol sale del usuario. En Android los usuarios empiezan con `caseta.`, `desem.` o `embar.` y ven solo sus módulos. | README, LoginMovil | BE-10, BE-14, FE-11 |
| R-02 | Las citas son de lunes a sábado, por andén de recibo (R1–R4), de 8:00 a 18:00, en bloques de 30 min, con duración de 1, 1.5, 2 o 3 h, sin pasar de las 18:00. El proveedor puede agendar a cualquier hora, cualquier día. | README, Proveedor, P-04 | BE-22 |
| R-03 | Dos citas no se empalman en el mismo andén. | README, Proveedor | BE-22 |
| R-04 | El folio de factura es obligatorio. Una factura puede cubrir varios productos, pero el mismo folio no se registra dos veces para el mismo producto. Un folio repetido se marca en rojo y bloquea la cita. | README, Proveedor, P-02 | BE-22, BE-23, FE-22 |
| R-05 | Un bulto lleva un solo producto (SKU). La factura se desglosa por bulto: producto, piezas, peso y volumen. | README, Bulto, Proveedor | BE-23 |
| R-06 | La etiqueta QR identifica bulto, OC, sucursal destino, SKU y piezas. Se descarga en PDF. | README, Bulto | BE-24 |
| R-07 | En recepción, un SKU que no está en la OC o un excedente **no se recibe** y se puede reportar al proveedor. | README, Desembarque | BE-32, BE-33 |
| R-08 | Caja de tarima por peso del bulto: roja ≥ 15 kg (abajo), naranja ≥ 7 y < 15 kg (en medio), verde < 7 kg (arriba). | README, `bundle.js · zona()` | BE-40, FE-02 |
| R-09 | Tarima de 1.12 × 1.15 m, altura máxima 2.00 m y 1,000 kg. Capacidad de volumen: 1.12 × 1.15 × 2.00 = 2.576 m³. No se agrega un bulto que exceda peso, volumen o altura. Una tarima se puede cerrar con cualquier porcentaje de llenado. | README, Tarima3D, P-06, P-11 | BE-40 |
| R-10 | El tortón lleva 12 tarimas, con capacidad de 12,000 kg y 30.91 m³ (12 × 2.576). Sale cuando llega al 90 %: primero se revisa el volumen (≥ 27.82 m³) y, si no, el peso (≥ 10,800 kg). El peso nunca pasa de 12,000 kg. Las tarimas se pueden cargar de forma desigual mientras el tortón cumpla la regla. | README, Embarque, P-05, P-11 | BE-41 |
| R-11 | Cada embarque genera su Relación de Embarque con QR, impresa y en PDF. | README, Embarque | BE-42 |
| R-12 | Folios con prefijo: `OC-`, `FAC-`, `B-`, `T-`, `EMB-`. | README | BE-04 |
| R-13 | Andenes: R1–R4 de recibo y E1–E3 de embarque. Check-in ocupa el andén y check-out lo libera. | Caseta | BE-30, BE-31 |
| R-14 | Seguimiento del pedido en 6 pasos: OC emitida, Proveedor, En CEDIS, En tarima, En camino, Recibido. La sucursal recibe escaneando el QR de la relación. | Sucursal | BE-20, BE-43 |
| R-15 | Cada sucursal tiene un rack (`R-<clave>`). El CEDIS tiene 32 racks. | Oficina | BE-13, BE-40 |
| R-16 | Una OC puede tener productos de varios proveedores y un proveedor participa en varias OC (relación muchos a muchos a través de las líneas de la OC). Cada proveedor agenda, factura y entrega solo su parte. | P-07 | BE-20, BE-21 |
| R-17 | Los usuarios nuevos reciben una contraseña temporal y deben cambiarla en su primer inicio de sesión. | P-08 | BE-15, FE-44 |

---

## 6. Decisiones de arquitectura

| # | Decisión | Motivo |
|---|---|---|
| A-01 | Una sola app Vue con dos layouts: móvil (roles Android) y web (Sucursal, Proveedor, Oficina). | Un repositorio, un build y un despliegue; los componentes base se comparten. |
| A-02 | El canal Android es la misma app web, responsiva: el layout móvil ocupa el ancho del dispositivo y se prueba en varios tamaños de teléfono. | Respuesta P-01. |
| A-03 | Los estilos se toman tal cual de `tokens.css` y `bundle.css`. No se usa Vuetify, Tailwind ni otra librería de UI. | Es la forma más segura de quedar idénticos al prototipo. |
| A-04 | Ilustraciones SVG copiadas sin modificar y Poppins servida desde el propio front. | El prototipo prohíbe recortar o recolorear; no depender de Google Fonts en la bodega. |
| A-05 | La Tarima 3D se hace con transformaciones CSS 3D, igual que el prototipo, sin Three.js. | Mismo resultado visual y menos peso en teléfonos Android. |
| A-06 | Back monolítico en FastAPI, organizado por dominio (`auth`, `catalogos`, `pedidos`, `citas`, `recepcion`, `tarimas`, `embarques`, `avisos`). | Un solo servicio es suficiente y más simple de desplegar. |
| A-07 | Las reglas de negocio viven en el back; el front solo las refleja. | Evita que una validación hecha solo en pantalla se pueda saltar. |
| A-08 | El empalme de citas se impide en PostgreSQL con una restricción `EXCLUDE` sobre rango de tiempo por andén. | Dos proveedores no pueden ganar el mismo hueco aunque confirmen al mismo tiempo. |
| A-09 | Autenticación con JWT y contraseñas con Argon2. El rol se guarda en la base; el prefijo del usuario solo se valida al crearlo. | El rol no puede depender de cómo se escribe el usuario al iniciar sesión. |
| A-10 | El back genera los PDF (etiquetas y relación) y los QR reales. | Mismo documento para descargar e imprimir; el QR del prototipo es ilustrativo. |
| A-11 | Las pantallas operativas y los avisos se actualizan por consulta periódica cada 15 s. | Suficiente para la operación y sin infraestructura de WebSockets. |
| A-12 | **Contrato primero:** el back publica el contrato de cada sprint en `docs/api/` antes de que empiece; DevOps crea los servicios de Axios con modo mock; el front consume solo `@/api`. | Las tres áreas avanzan en paralelo sin esperarse. |
| A-13 | El escaneo usa la cámara del teléfono desde el navegador. | No hay lector dedicado en alcance. Requiere HTTPS (DO-12). |
| A-14 | Todo corre dentro de una instancia EC2: front con Nginx, back con Uvicorn y PostgreSQL, en contenedores con volumen persistente. | Respuesta P-09. |
| A-15 | `main` es producción: cada merge a `main` actualiza la instancia. `dev` se publica como staging en la misma instancia, en otro subdominio. | Respuesta P-12: el producto queda funcional desde `main`. Staging permite probar en teléfonos antes de cerrar el sprint. |
| A-16 | Las líneas de la OC llevan producto y proveedor. Cada producto tiene un proveedor principal en el catálogo, que se usa al crear la OC. | Respuesta P-07 sin agregar pantallas. |

---

## 7. Hallazgos del prototipo

Errores o huecos que **no se copian**. Las rutas son relativas a `design/CEDIS Flow/`.

| # | Hallazgo | Ubicación | Qué se hace |
|---|---|---|---|
| H-01 | La capacidad del tortón aparece como 11,000 kg. | `components/Embarque/preview.html` (`CAPK=11000`) | Resuelto: 12,000 kg (P-05). |
| H-02 | El volumen se calcula distinto en Tarima3D (altura útil, 2.19 m³) y en Embarque (altura total, 28.59 m³). | `Tarima3D/preview.html` (`CAP_M3`), `Embarque/preview.html` (`CAPV`) | Resuelto: tarima de 2.00 m, 2.576 m³ por tarima y 30.91 m³ por tortón (P-06). |
| H-03 | LoginMovil detecta el rol con `cas`, `des` y `emb`, más corto que los prefijos documentados. | `LoginMovil/preview.html` (`detect`) | El rol lo devuelve el back. El chip se muestra con los prefijos completos. |
| H-04 | «Recepción cerrada · 24 bultos» está fijo en el texto. | `Desembarque/preview.html` | Se muestra el número real de bultos recibidos. |
| H-05 | «+ Bulto» agrega siempre clips, sin formulario. | `Proveedor/preview.html` (`facv`) | Resuelto: formulario con los atributos del producto (P-03). |
| H-06 | El calendario muestra Mar–Sáb con fechas fijas. | `Proveedor/preview.html` (`DN`, `DD`) | Resuelto: lunes a sábado con fechas reales (P-04). |
| H-07 | El folio repetido solo se compara dentro del mismo proveedor. | `Proveedor/preview.html` (`usados`) | Resuelto: único por folio y producto (P-02). |
| H-08 | El QR es decorativo: no codifica datos. | `components/bundle.js` (`qr`) | QR real generado en back (A-10). |
| H-09 | Ninguna pantalla define quién asigna proveedores a la OC. | `Flujo/preview.html`, `Oficina/preview.html` | Resuelto: relación muchos a muchos por línea (P-07, A-16). |
| H-10 | El formulario de Usuarios no pide contraseña y el rol es texto libre. | `Oficina/preview.html` (`form`) | Resuelto: rol de una lista fija y contraseña temporal (P-08). |
| H-11 | Eliminar en Oficina borra el registro, aunque tenga historial. | `Oficina/preview.html` (`del`) | El back no borra registros con historial: los marca como inactivos. |
| H-12 | Campana de avisos, pestañas inferiores, búsqueda en encabezados, «Recordarme» y «¿Olvidaste tu contraseña?» no tienen pantalla. | Caseta, Desembarque, Embarque, Sucursal, Proveedor, LoginWeb | Resuelto: entran en alcance como pantallas nuevas (P-10). |
| H-13 | KPIs con valores fijos (23 / 35 camiones, 92 % a tiempo, 3.2 días, etc.). | Oficina, Proveedor, Sucursal | El back los calcula (BE-44). |
| H-14 | «Cerrar tarima» por debajo del 90 % no dice si cierra. | `Tarima3D/preview.html` (`close`) | Resuelto: se puede cerrar con cualquier porcentaje (P-11). |
| H-15 | La relación de embarque muestra 4 tarimas y «… n tarimas». | `Embarque/preview.html` | La vista en pantalla queda igual; el PDF lista todas. |
| H-16 | Las vistas previas no cargan `tokens.css`, `bundle.css` ni `bundle.js`, y las imágenes apuntan a `/_blob/<id>`. | Todos los `preview.html` | DevOps crea un visor local (DO-06) sin tocar `design/`. |
| H-17 | `R-01` nombra tanto un andén (R1) como un rack (R-01). | Caseta, Oficina | Se conserva el texto; en el back son entidades distintas. |
| H-18 | La regla de zona dice «7–15 kg» para la caja naranja, pero el código manda los bultos de 15 kg exactos a la roja. | README, `bundle.js · zona()` | Se sigue el código: ≥ 15 kg es roja (R-08). |
| H-19 | Desembarque y Embarque tienen botón de regresar, pero no existe la pantalla anterior para elegir la OC o el embarque. | `Desembarque/preview.html`, `Embarque/preview.html` | Mientras se diseña la pestaña «Inicio» (FE-54), la OC se abre al escanear su primer bulto y el embarque al escanear su primera tarima. |
| H-20 | El aviso del tortón dice «Listo para salir · peso y volumen ≥ 90 %», pero la regla ahora es volumen primero y luego peso (R-10). | `Embarque/preview.html` | Pregunta N-01. |

---

## 8. Preguntas y respuestas del Product Owner

### Respondidas el 2026-11-25

| # | Pregunta | Respuesta |
|---|---|---|
| P-01 | ¿El canal Android es app nativa o web? | Web responsiva que se adapta a las medidas del dispositivo. |
| P-02 | ¿El folio de factura es único por proveedor o global? | Único por folio y producto: una factura puede cubrir varios productos, pero no se registra dos veces el mismo folio para el mismo producto. |
| P-03 | ¿Cómo se captura un bulto? | Con los mismos atributos del producto: producto, SKU, piezas, peso y volumen. |
| P-04 | ¿Qué días se agendan citas? | Las citas son de lunes a sábado; el proveedor puede agendar 24/7. Se pueden agendar hasta 2 semanas adelante (criterio por defecto). |
| P-05 | ¿Capacidad en peso del tortón? | 12,000 kg. |
| P-06 | ¿Con qué altura se calcula el volumen? | 2.00 m, para redondear. |
| P-07 | ¿Quién asigna proveedores a la OC? | Relación muchos a muchos: una OC tiene varios proveedores y un proveedor está en varias OC. |
| P-08 | ¿Contraseña y rol al crear usuarios? | Contraseña temporal y cambio obligatorio después del primer inicio de sesión. |
| P-09 | ¿Base de producción en EC2 o RDS? | Todo dentro de la instancia EC2. |
| P-10 | ¿Avisos, perfil, búsqueda y recuperación? | Sí, todo. El perfil es sencillo: quién es y su usuario. La recuperación pasa por Oficina (criterio por defecto, sin correo): el usuario la solicita, Oficina genera una contraseña temporal y el usuario la cambia al entrar. |
| P-11 | ¿Se cierra una tarima por debajo del 90 %? | Sí. El límite del 90 % es del tortón; las tarimas se llenan hasta su capacidad. |
| P-12 | ¿Cómo se publica el producto? | `main` está enlazado a producción y la instancia se actualiza con cada merge a `main`. |

### Abiertas

| # | Pregunta | Criterio por defecto | Afecta |
|---|---|---|---|
| N-01 | Con la regla de volumen primero y luego peso, ¿cómo queda el aviso «Listo para salir · peso y volumen ≥ 90 %»? | «Listo para salir · volumen o peso ≥ 90 %». | FE-41 |
| N-02 | Los botones «Probar como» del login móvil llenan usuarios de demostración. ¿Se muestran en producción? | Solo en staging y desarrollo. | FE-11 |

---

## 9. Definition of Ready

Una historia entra al sprint cuando:

- Tiene ID del área, formato «Como… quiero… para…», criterios de aceptación y puntos (máximo 8).
- Se sabe qué pantalla del prototipo cubre o, si es una pantalla nueva, Ximena aprobó su diseño.
- Su contrato de API está publicado en `docs/api/`, si consume o expone datos.
- Sus dependencias de otras áreas están hechas o tienen mock.
- No toca archivos de otra área (ver [Propiedad de archivos](#propiedad-de-archivos)).

## 10. Definition of Done

- Se cumplen todos los criterios de la historia.
- Pasan lint, pruebas y build del servicio modificado, en local y en CI.
- **Front:** la pantalla se compara lado a lado con el prototipo en el visor (DO-06) y queda igual, en escritorio y en tamaños de teléfono. La captura va en el PR.
- **Back:** las reglas de negocio tienen pruebas con la base de pruebas de PostgreSQL y el endpoint coincide con el contrato.
- **DevOps:** el cambio está probado en staging o en CI.
- No se suben secretos, `.env`, bases de datos ni datos reales.
- El PR del área queda abierto hacia `dev`, listo para revisión.

---

## Coordinación entre áreas

### Ramas, commits y PR

- Rama por área y sprint, desde `dev`: `<área>-<tipo>/sprint<N>`. Ejemplos: `front-feat/sprint1`, `back-feat/sprint2`, `devops-ci/sprint1`, `back-fix/sprint3`.
- Tipos: `feat`, `fix`, `test`, `docs`, `refactor`, `style`, `chore`, `ci`.
- Commits con Conventional Commits en español. El alcance es el área: `feat(front): …`, `feat(back): …`, `ci(devops): …`. Una historia por commit.
- Un PR por área y sprint hacia `dev`. Título: `feat(front): login, oficina y catálogos (sprint 1)`.
- `dev` → `main` al cerrar cada sprint; ese merge actualiza producción. El merge lo hace el usuario desde GitHub.

### Propiedad de archivos

Cada archivo tiene un solo dueño. Un agente no edita archivos de otra área.

| Ruta | Dueño |
|---|---|
| `front/src/views/`, `components/`, `layouts/`, `stores/`, `router/`, `styles/`, `assets/`, `composables/` | Front |
| `front/index.html`, `front/public/`, `front/package.json` y su lock | Front |
| `front/src/api/` (cliente Axios, servicios y mocks), `front/vite.config.js`, `front/.env.example` | DevOps |
| `back/` (código, migraciones, pruebas, `pyproject.toml`, `.env.example`) | Back |
| `compose.yaml` (PostgreSQL en Podman para desarrollo) | Back |
| `docs/api/` (contratos de API) | Back |
| `.github/`, `infra/`, `tools/`, `Dockerfile` y `.dockerignore` de front y back, `front/nginx.conf.template` | DevOps |
| `docs/scrum/front.md`, `back.md`, `devops.md` | El área de cada archivo |
| `docs/AVISOS-front.md`, `AVISOS-back.md`, `AVISOS-devops.md` | Buzón del área: cualquier área agrega avisos; solo la dueña cambia su estado ([AVISOS.md](AVISOS.md)) |
| `docs/scrum.md`, `docs/AVISOS.md`, `README.md`, `.gitignore`, `.editorconfig`, `docs/AGENTE.md`, `CLAUDE.md` | Compartidos: se cambian solo con acuerdo del equipo |
| `design/` | Nadie. Solo lectura |

Excepción: si DevOps necesita una dependencia en `front/package.json` (por ejemplo Axios), la agrega en el sprint 0 antes de que front empiece, y lo avisa.

### Contrato primero

1. En el sprint N, el back publica el contrato del sprint N+1 en `docs/api/sprint-<N+1>.md`: rutas, cuerpos, respuestas y errores.
2. Al iniciar el sprint N+1, DevOps crea los servicios de Axios y sus mocks con ese contrato (`VITE_API_MOCK=true`).
3. El front construye las pantallas contra `@/api`, sin esperar al back.
4. Cuando el back termina un endpoint, DevOps cambia el servicio a la API real y lo prueba en staging.

### Pedir algo a otra área

Se abre un issue en GitHub con la etiqueta del área (`front`, `back` o `devops`) y la historia que lo necesita. El área dueña decide si entra a su sprint o a su backlog. Lo que surge a mitad de sprint va al backlog, no al sprint en curso.

---

## Sprints

| Sprint | Objetivo | Front | Back | DevOps |
|---|---|---|---|---|
| 0 | Configuración y base visual | FE-01…05 | BE-01…05 | DO-01…06 |
| 1 | Acceso por rol, catálogos de Oficina y producción desde `main` | FE-10…14 | BE-10…16 | DO-10…14 |
| 2 | Pedido de sucursal, cita y factura del proveedor | FE-20…23 | BE-20…25 | DO-20…23 |
| 3 | Caseta, recepción y detalle de bulto | FE-30…33 | BE-30…35 | DO-30…33 |
| 4 | Tarima, embarque, recepción en sucursal, indicadores y perfil | FE-40…44 | BE-40…45 | DO-40…43 |
| 5 | Complementos: recuperación, avisos, búsqueda y pestañas móviles | FE-50…54 | BE-50…53 | DO-50…51 |

### Demo por rol al cierre de cada sprint

| Sprint | Demo |
|---|---|
| 0 | El equipo ve el prototipo en el visor local, la página de Elementos del front idéntica, la base en Podman con semillas y el CI corriendo en un PR. |
| 1 | Oficina inicia sesión y administra los catálogos. Caseta, desembarque y embarque entran desde el teléfono y ven solo sus módulos. Todo en producción, publicado desde `main`. |
| 2 | Sucursal arma un pedido con productos de dos proveedores. Cada proveedor agenda su cita sin empalmes, captura su factura por bulto y descarga etiquetas QR en PDF. |
| 3 | Caseta registra la entrada con el QR de la cita. Desembarque escanea bultos, rechaza un excedente y cierra la recepción. Se consulta el detalle del bulto. |
| 4 | Desembarque arma la tarima 3D por peso. Embarque llena el tortón al 90 % e imprime la relación. Caseta registra la salida y la sucursal recibe con el QR. Oficina ve los indicadores reales. Un usuario nuevo cambia su contraseña temporal y consulta su perfil. |
| 5 | Un usuario recupera su contraseña con ayuda de Oficina. Cada rol recibe sus avisos, busca en su portal y usa las pestañas inferiores del móvil. |

---

## Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| La cámara del navegador solo funciona con HTTPS. | Sin escaneo no hay caseta, recepción ni embarque. | DO-12 entrega HTTPS desde el sprint 1; en local se usa `localhost`. |
| Las pantallas nuevas no tienen diseño. | Se retrasan o se inventan. | Ximena diseña cada pantalla nueva un sprint antes con el sistema del prototipo (DoR). |
| El contrato de API llega tarde. | Front y DevOps se detienen. | Contrato del siguiente sprint como historia del sprint actual (BE-05, BE-16, BE-25, BE-35, BE-45). |
| Producción se actualiza con cada merge a `main`. | Un error llega directo a los usuarios. | CI obligatorio, staging desde `dev` y vuelta a la versión anterior (DO-41). |
| La Tarima 3D es lenta en teléfonos de gama baja. | Mala experiencia en bodega. | CSS 3D sin librerías (A-05); se prueba en un Android real en el sprint 4. |
| Diferencias visuales pequeñas que nadie nota. | Se rompe la regla del prototipo. | Comparación lado a lado en cada PR de front y comparación automática en CI (DO-22). |
| La carga de front es la más alta (hasta 29 puntos). | El front se vuelve el cuello de botella. | Revisar la velocidad al cerrar el sprint 1 y mover historias de pantallas nuevas al backlog si hace falta. |
| Calendario y velocidad sin confirmar. | El plan no cabe en el tiempo del reto. | Revisar la carga al cerrar el sprint 1. |
