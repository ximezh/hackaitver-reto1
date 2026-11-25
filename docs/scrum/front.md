# Plan Scrum · Front

**Responsable:** Ximena Zaleta y su agente
**Abarca:** UI/UX, interfaces, componentes y layouts en `front/`
**IDs:** `FE-NN` · **Épicas:** `FE-E1…` · **Ramas:** `front-<tipo>/sprint<N>` · **Commits:** `tipo(front): …`

Reglas generales, hallazgos, preguntas, DoR y DoD: [docs/scrum.md](../scrum.md).

## Reglas de esta área

- **Cada pantalla es idéntica al prototipo** en `design/CEDIS Flow/components/<Pantalla>/preview.html`: textos, colores, tamaños, espacios, íconos, ilustraciones y animaciones. Solo cambia si Ximena, Jesus o Luis Daniel lo autorizan; se anota en `docs/scrum.md`.
- Los valores visuales salen de `tokens.css` y `components/bundle.css`. No se inventan colores, tamaños ni sombras.
- Las pantallas leen datos solo con `@/api` (lo mantiene DevOps). No se importa Axios en vistas ni stores.
- Mientras el back no termina, se trabaja con los mocks (`VITE_API_MOCK=true`).
- Archivos propios: `front/src/views`, `components`, `layouts`, `stores`, `router`, `styles`, `assets`, `composables`, `front/index.html`, `front/public`, `front/package.json`.
- Antes de abrir el PR: comparar cada pantalla con el prototipo en el visor (DO-06) y adjuntar la captura.

## Épicas

| Épica | Nombre | Historias |
|---|---|---|
| FE-E1 | Base visual | FE-01…05 |
| FE-E2 | Acceso y Oficina | FE-10…14 |
| FE-E3 | Pedido y proveedor | FE-20…23 |
| FE-E4 | Operación en bodega | FE-30…33 |
| FE-E5 | Tarima, embarque y cierre | FE-40…44 |
| FE-E6 | Complementos | FE-50…54 |

---

## Sprint 0 · Base visual

**Objetivo:** tener los tokens, componentes y layouts del prototipo listos para construir pantallas.
**Rama:** `front-chore/sprint0` · **Puntos:** 18

### FE-01 · Tokens, tipografía e ilustraciones · 3 pts
Como desarrolladora de front quiero los tokens, la fuente y las ilustraciones del prototipo dentro de la app para que todas las pantallas usen exactamente los mismos valores.
- `tokens.css` se copia sin cambiar valores a `front/src/styles/tokens.css` y se carga en `main.js`.
- Poppins (400, 500, 600, 700) se sirve desde el propio front, sin Google Fonts.
- Las 14 ilustraciones de `assets/Ilustraciones/` se copian sin modificar a `front/src/assets/ilustraciones/`.
- Se elimina el CSS de ejemplo de Vue (`base.css`, `main.css`).

### FE-02 · Íconos y utilidades visuales · 3 pts
Como desarrolladora de front quiero los íconos y ayudas de `bundle.js` como piezas de Vue para no repetir trazos ni reglas.
- Componente `Icono` con los 50 trazos de `bundle.js`: 24 px de caja, trazo 1.8, puntas redondeadas, tamaño y grosor configurables.
- `zona(kg)` y `zonas` con la regla R-08, y `formatoKg()` con `es-MX`. Con pruebas de los límites 7 y 15 kg.
- Componente `CodigoQr` que dibuja un QR real a partir de un texto, con el mismo tamaño y colores del prototipo.

### FE-03 · Layouts móvil y web · 5 pts
Como usuario quiero que la app tenga la misma estructura del prototipo para reconocer cada pantalla.
- `LayoutMovil`: barra superior (`appbar`), zona con scroll, barra inferior (`tabbar`), botón flotante (`fab`), hoja inferior (`sheet`) y aviso (`toast`), con las medidas de `bundle.css`.
- El layout móvil ocupa el ancho del dispositivo (web responsiva, P-01). Se revisa en 360, 390 y 412 px de ancho.
- `LayoutWeb`: barra lateral de 232 px con marca, navegación y tarjeta de usuario; encabezado con título, búsqueda y campana; contenido.
- El marco del teléfono y la barra de estado «9:41» no se dibujan (cambio autorizado).
- Composable `useToast` con la misma duración (1.9 s) y animación.

### FE-04 · Componentes base (Elementos) · 5 pts
Como desarrolladora de front quiero los elementos base del prototipo para armar cualquier pantalla.
- `BotonBase` (primary, soft, line, danger, ok; `sm`, `block`, deshabilitado), `Chip` (normal, ok, warn, bad, mute), `CampoTexto` con ícono, `Segmentado`, `BarraAvance` (valor y tope), `ZonasTarima`.
- Una ruta `/elementos` (solo en desarrollo) reproduce `components/Elementos/preview.html` y queda idéntica.
- Pruebas con Vitest de variantes y estados.

### FE-05 · Limpieza del andamiaje y rutas · 2 pts
Como desarrolladora de front quiero quitar el ejemplo de Vue y tener las rutas de la app para empezar el sprint 1 sin basura.
- Se eliminan `HelloWorld`, `TheWelcome`, `WelcomeItem`, los íconos de ejemplo, `AboutView` y el store `counter`.
- Rutas: `/login` (web), `/movil/login`, y grupos `/movil/*` y `/web/*` con sus layouts.
- Lint, pruebas y build pasan.

---

## Sprint 1 · Acceso y Oficina

**Objetivo:** cada rol inicia sesión y ve solo sus módulos; Oficina administra los catálogos.
**Rama:** `front-feat/sprint1` · **Puntos:** 26 · **Depende de:** DO-10, DO-11 (servicios y mocks)

### FE-10 · LoginWeb · 5 pts
Como usuario de sucursal, proveedor u oficina quiero iniciar sesión en la web para entrar a mi portal.
- Igual a `LoginWeb/preview.html`: panel azul con ilustración, lema y puntos; pestañas Sucursal, Proveedor y Oficina; placeholder por rol.
- Usuario o contraseña incorrectos muestran el aviso del prototipo.
- Al entrar, redirige al portal del rol que devuelve el back.
- «Recordarme» define si la sesión se guarda; «¿Olvidaste tu contraseña?» se dibuja sin acción (P-10).

### FE-11 · LoginMovil · 5 pts
Como trabajador del CEDIS quiero iniciar sesión en el teléfono para ver solo los módulos de mi rol.
- Igual a `LoginMovil/preview.html`: ilustración, campos de 48 px, mostrar contraseña, chip de rol con «CEDIS Veracruz».
- El chip aparece con los prefijos completos `caseta.`, `desem.`, `embar.` (H-03).
- Bienvenida con los tres módulos del rol y botón «Salir».
- «Probar como» solo aparece fuera de producción (N-02).

### FE-12 · Portal de Oficina e indicadores · 5 pts
Como usuario de oficina quiero ver los indicadores del día y la ocupación de racks al entrar.
- Igual a `Oficina/preview.html`: navegación con conteo por catálogo, chip de fecha, tres KPIs y la tarjeta de 32 racks en 16 columnas.
- Los valores vienen de `@/api` (mock hasta BE-44).

### FE-13 · CRUD de catálogos · 8 pts
Como usuario de oficina quiero crear, editar, buscar y eliminar productos, proveedores, sucursales y usuarios.
- Tabla con búsqueda, conteo de registros, botón «Nuevo», editar y eliminar, chip de estado y miniatura del producto.
- Modal «Nuevo / Editar» en dos columnas y confirmación «¿Eliminar?», con los avisos del prototipo.
- La fila creada o editada parpadea como en el prototipo.
- Los errores de validación del back se muestran en el campo.

### FE-14 · Sesión y guardas por rol · 3 pts
Como usuario quiero que la app me lleve solo a mis pantallas y me saque al cerrar sesión.
- Store de sesión con usuario, rol y canal.
- Las rutas de otro rol o canal redirigen al inicio del rol.
- Sin sesión, cualquier ruta lleva al login de su canal.

---

## Sprint 2 · Pedido y proveedor

**Objetivo:** la sucursal pide y sigue su pedido; el proveedor agenda su cita y captura la factura por bulto.
**Rama:** `front-feat/sprint2` · **Puntos:** 29 · **Depende de:** DO-20, DO-21

### FE-20 · Sucursal · Pedir · 8 pts
Como sucursal quiero pedir por bultos viendo cada producto para armar mi pedido sin errores.
- Igual a la vista «Pedir» de `Sucursal/preview.html`: catálogo con imagen, SKU, bulto de N piezas y contador.
- Tarjeta «Tu pedido» fija con bultos, peso estimado y «Enviar pedido» deshabilitado si está vacío.
- Al enviar, muestra el aviso con el folio de la OC y pasa a «En camino».

### FE-21 · Sucursal · En camino · 5 pts
Como sucursal quiero ver en qué paso va cada pedido para saber cuándo llega.
- Tarjeta por pedido con folio, fecha, bultos, embarque y chip «Llega …».
- Seguimiento de 6 pasos con hecho, actual y pendiente (R-14).
- Conteo de pedidos en la navegación.
- «Recibir con QR» aparece en el paso «En camino» (la acción se completa en FE-42).

### FE-22 · Proveedor · Agendar cita · 8 pts
Como proveedor quiero elegir andén y horario en un calendario para agendar mi entrega sin empalmes.
- Igual a la vista «Agendar cita» de `Proveedor/preview.html`: OC, folio de factura, duración, resumen y calendario de 4 andenes × 20 medias horas.
- Días de lunes a sábado con fechas reales, hasta 2 semanas adelante (R-02, cambio autorizado). Ximena define cómo se pasa a la semana siguiente.
- La lista de OC muestra solo las del proveedor de la sesión, con los bultos de su parte (R-16).
- Bloques ocupados, «Tu cita» en azul y en rojo si choca.
- «Ese andén ya está ocupado», «Este folio ya está registrado» y «El folio es obligatorio» como en el prototipo; «Confirmar cita» deshabilitado mientras haya error.
- El folio se valida con la regla de folio y producto (R-04). La validación final es del back.

### FE-23 · Proveedor · Factura y bultos · 8 pts
Como proveedor quiero ver mi factura desglosada por bulto y descargar las etiquetas para pegarlas en cada bulto.
- KPIs de factura, bultos (x de N), peso y volumen.
- Tabla con bulto, producto, SKU, piezas, peso, volumen y botón de etiqueta.
- Vista de etiquetas con QR real, y «Etiquetas (PDF)» que descarga el PDF del back.
- «+ Bulto» abre un formulario con producto, SKU, piezas, peso y volumen (P-03), con el estilo del modal de Oficina. Ximena aprueba el diseño.

---

## Sprint 3 · Operación en bodega

**Objetivo:** caseta registra camiones y desembarque recibe bultos contra la OC.
**Rama:** `front-feat/sprint3` · **Puntos:** 26 · **Depende de:** DO-30, DO-31

### FE-30 · Caseta · 8 pts
Como caseta quiero ver los andenes y las citas del día y registrar entradas y salidas de camiones.
- Igual a `Caseta/preview.html`: KPIs Dentro, Por llegar y Salieron; 7 andenes con leyenda; Entradas y Salidas.
- Tarjetas con hora, andén, proveedor o sucursal, placa y chip (Descargando, Cargando, Salió, +N min, A tiempo).
- Hoja de check-in con operador y sello, y de check-out con sello y documentos.
- El botón QR abre el escáner y, al leer la cita, abre su check-in.

### FE-31 · Escáner de QR · 5 pts
Como trabajador del CEDIS quiero escanear con la cámara del teléfono para no capturar folios a mano.
- Componente con el marco y la línea animada del prototipo.
- Usa la cámara trasera y devuelve el texto leído.
- Si no hay permiso de cámara, muestra un aviso con el estilo del prototipo.
- Se usa en Caseta, Desembarque, Tarima, Embarque y Sucursal.

### FE-32 · Desembarque · 8 pts
Como supervisor de desembarque quiero escanear cada bulto contra la OC para saber al momento qué se recibe y qué no.
- La OC se abre al escanear su primer bulto, mientras no exista la pestaña «Inicio» (H-19).
- Igual a `Desembarque/preview.html`: anillo de avance, chips Recibidos, Faltan y Rechazados, botón «Escanear bulto».
- Líneas de la OC con miniatura, barra y conteo.
- Hoja «Bulto recibido» con su caja de tarima, y «No se recibe» con «Excedente» o «SKU no solicitado» y «Reportar al proveedor».
- «Cerrar recepción y armar tarima» con el número real de bultos (H-04).

### FE-33 · Bulto · 5 pts
Como supervisor quiero ver un bulto primero en imagen y luego su detalle para identificarlo rápido.
- Igual a `Bulto/preview.html`: carrusel de 3 imágenes con deslizamiento y paso al siguiente bulto de la factura.
- Tira de bultos, chips «1 SKU por bulto» y «En la OC».
- «Ver más» con el desglose completo y la etiqueta QR con «Descargar etiqueta».

---

## Sprint 4 · Tarima, embarque y cierre

**Objetivo:** armar tarimas, llenar el tortón, imprimir la relación y cerrar el ciclo en la sucursal.
**Rama:** `front-feat/sprint4` · **Puntos:** 27 · **Depende de:** DO-40

### FE-40 · Tarima 3D · 8 pts
Como supervisor quiero ver la tarima en 3D con las cajas por peso para acomodar bien los bultos.
- Igual a `Tarima3D/preview.html`, con CSS 3D (A-05): tarima de madera, cajas roja, naranja y verde, emplaye y plano de altura máxima.
- Girar arrastrando, girar 45°, separar cajas y vista inicial.
- Medidores con los topes nuevos: 1,000 kg, 2.58 m³ y 2.00 m; el indicador «Máx.» dice 2.00 m (cambio autorizado).
- Tarjetas por caja y lista de bultos; la tarima se puede cerrar con cualquier porcentaje (P-11).
- «Escanear bulto» con la animación del bulto volando a su caja; aviso si excede la capacidad.
- Se prueba en un Android real.

### FE-41 · Embarque · 8 pts
Como supervisor de embarque quiero llenar el tortón y generar la relación cuando llegue al 90 %.
- Igual a `Embarque/preview.html`: tortón con 12 lugares, medidores de peso y volumen, aviso de la regla del 90 %.
- Porcentajes sobre 12,000 kg y 30.91 m³; el aviso sigue la regla de volumen primero y luego peso (R-10, N-01).
- El embarque se abre al escanear su primera tarima, mientras no exista la pestaña «Inicio» (H-19).
- Lista de tarimas con Verificada, Cargada o En rack; «Verificar» con el escáner.
- «Relación» deshabilitado hasta cumplir R-10; hoja con QR, PDF e Imprimir.
- No deja cargar una tarima que haga pasar el tortón de 12,000 kg.

### FE-42 · Sucursal · Recibir con QR · 3 pts
Como sucursal quiero recibir mi pedido escaneando el QR de la relación para cerrar el pedido.
- «Recibir con QR» abre el escáner, envía el folio y marca el paso «Recibido».
- Aviso «EMB-… recibido · N bultos».

### FE-43 · Historiales · 3 pts
Como sucursal o proveedor quiero ver mi historial e indicadores.
- Igual a las vistas «Historial» de `Sucursal/preview.html` y `Proveedor/preview.html`: KPIs y tabla con chip de estado.
- «Relación» descarga el PDF del embarque.

### FE-44 · Perfil y cambio de contraseña · 5 pts
Como usuario quiero cambiar mi contraseña temporal y ver mi perfil para usar una cuenta propia.
- Pantalla nueva (cambio autorizado) con el sistema del prototipo; Ximena aprueba el diseño.
- Si la sesión indica contraseña temporal, la app pide cambiarla antes de cualquier otra pantalla (R-17).
- Perfil sencillo: nombre, usuario y rol, con «Cambiar contraseña» y «Salir». En móvil es la pestaña «Perfil».

---

## Sprint 5 · Complementos

**Objetivo:** recuperación de contraseña, avisos, búsqueda y las pestañas móviles que faltaban.
**Rama:** `front-feat/sprint5` · **Puntos:** 24 · **Depende de:** DO-50
Todas son pantallas nuevas: se construyen con el sistema del prototipo y Ximena aprueba su diseño en el sprint 4.

### FE-50 · Recuperar contraseña · 3 pts
Como usuario quiero pedir una contraseña nueva cuando olvido la mía.
- «¿Olvidaste tu contraseña?» abre una pantalla para escribir el usuario y enviar la solicitud a Oficina.
- Oficina ve la solicitud en sus avisos y genera la contraseña temporal desde Usuarios.
- Mensaje de confirmación que no revela si el usuario existe.

### FE-51 · Avisos · 5 pts
Como usuario quiero ver los avisos de mi rol desde la campana para no perderme nada.
- La campana muestra el número de avisos sin leer y abre un panel con la lista.
- Marcar como leído; tocar un aviso lleva a su pantalla.
- Se actualiza cada 15 s (A-11).

### FE-52 · Búsqueda en portales web · 3 pts
Como sucursal o proveedor quiero buscar desde el encabezado para encontrar rápido un pedido, producto, OC o factura.
- «Buscar producto o pedido» en Sucursal y «Buscar OC o factura» en Proveedor muestran resultados y abren el elegido.

### FE-53 · Pestañas de caseta · 5 pts
Como caseta quiero las pestañas Citas e Historial para consultar fuera del día actual.
- Citas: citas por día y andén. Historial: entradas y salidas anteriores con placa y hora.
- «Perfil» usa FE-44.

### FE-54 · Pestañas de desembarque y embarque · 8 pts
Como supervisor quiero las pestañas Inicio, Tarimas e Historial para moverme entre mis tareas.
- Inicio: OC por recibir (desembarque) o embarques por cargar (embarque) del día; desde ahí se abre la pantalla de trabajo (H-19).
- Tarimas: tarimas armando y cerradas, con acceso a la Tarima 3D.
- Historial: recepciones o embarques anteriores.

---

## Backlog de front

| ID | Historia | Origen |
|---|---|---|
| — | Sin historias todavía | — |

## Avance

| Sprint | Estado | PR |
|---|---|---|
| 0 | Pendiente | — |
| 1 | Pendiente | — |
| 2 | Pendiente | — |
| 3 | Pendiente | — |
| 4 | Pendiente | — |
| 5 | Pendiente | — |
