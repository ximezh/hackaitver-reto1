# CEDIS Flow

Sistema de diseño e interfaces para digitalizar el flujo del CEDIS: **de la orden de compra al embarque**. Cubre los cuatro momentos de la operación (agendamiento, identificación, recepción, almacenamiento y embarque) con pantallas pensadas para cada trabajador.

## Principios

- **Primero la imagen, después el texto.** Cada pantalla abre con una referencia visual (ilustración isométrica, tarima 3D, camión, anillo de avance). El detalle aparece solo al pedirlo con «Ver más».
- **Una acción principal por pantalla.** En Android, la acción grande del pulgar siempre es azul (`brand-600`): *Escanear bulto*, *Verificar*, *Registrar entrada*.
- **Números con su límite.** Toda carga se muestra como avance contra su tope: `567 / 1,000 kg`, `1.11 / 1.85 m`, `94 %` contra la regla del 90 %.
- **Color con significado.** Azul = acción o en proceso; verde = correcto; ámbar = pendiente; rojo = no se recibe. Los colores de la tarima son exclusivos del peso.
- **Empresarial y tranquilo.** Fondo `surface-50`, tarjetas blancas, sombras suaves (`shadow-card`), radios generosos (`radius-lg`).

## Canales por rol

| Rol | Canal | Pantallas |
| --- | --- | --- |
| Caseta | Android | LoginMovil → Caseta (check-in, check-out, andenes) |
| Supervisor de desembarque | Android | Desembarque (escaneo contra OC) → Bulto → Tarima3D |
| Supervisor de embarque | Android | Embarque (tortón, regla 90 %, relación) → Tarima3D |
| Sucursal | Web | LoginWeb → Sucursal (pedir, en camino, historial) |
| Proveedor | Web | LoginWeb → Proveedor (agendar cita, factura y bultos, historial) |
| Oficina | Web | LoginWeb → Oficina (CRUD de productos, proveedores, sucursales y usuarios) |

El login detecta el rol por el usuario (`caseta.*`, `desem.*`, `embar.*`) y muestra solo los módulos de ese rol.

## Reglas de negocio reflejadas en la interfaz

- **Cita:** por andén, de 8:00 a 18:00, mínimo 1 h; el calendario no deja empalmar dos entregas en el mismo andén.
- **Factura:** cada OC lleva un folio de factura único; un folio repetido se marca en rojo y bloquea la cita.
- **Un producto por bulto:** la factura se desglosa por bulto (producto, piezas, peso, volumen). Nunca se mezclan SKUs en un bulto.
- **Etiqueta QR:** identifica bulto, OC, sucursal destino, SKU y piezas. El proveedor la descarga en PDF y la pega.
- **Recepción:** lo que no está en la OC (otro SKU o excedente) se reporta y **no se recibe**.
- **Tarima:** 1.12 × 1.15 m, 1.85 m de altura máxima, 1,000 kg. Los bultos se acomodan por peso: caja roja abajo (≥ 15 kg), naranja en medio (7–15 kg), verde arriba (< 7 kg).
- **Embarque:** el tortón (12 tarimas) no sale hasta tener al menos 90 % en peso **y** volumen. Cada embarque genera su Relación de Embarque impresa y en PDF, con QR.

## Fundamentos visuales

- **Tipografía:** Poppins (Google Fonts) en todos los textos. `display` 28/36 para títulos de bienvenida, `title` 20/28 para folios, `subtitle` 16/24 para títulos de tarjeta, `body` 14/22, `caption` 12/16 para la etiqueta de un dato y `data` 14/20 seminegrita para su valor.
- **Color:** `brand-600` #1f5fd6 sobre blanco (5.7:1). Texto `ink` sobre `surface-0`; secundario `ink-muted`. Estados con fondo suave: `success`/`success-50`, `warning`/`warning-50`, `danger`/`danger-50`.
- **Tarima:** `pallet-heavy`, `pallet-mid`, `pallet-light` llevan una retícula de cajas encima; sobre naranja el texto es oscuro (#3a2300).
- **Espacio:** márgenes móviles `space-4` (16 px), entre secciones `space-6`, página web `space-8`.
- **Formas:** botones y campos `radius-md` (48 px de alto en móvil para usar con guantes), tarjetas `radius-lg`, chips `radius-pill`.

## Iconografía e ilustraciones

- Íconos de línea de 24 px, trazo 1.8 y puntas redondeadas (`Cedis.ic(nombre)` en `components/bundle.js`).
- Ilustraciones isométricas hechas con el kit [Drakaniia/isometric](https://github.com/Drakaniia/isometric) en estilo *Two-tone* con el azul de marca como acento: CEDIS, sucursal, andén, caseta, embarque, agenda, impresora, base de datos y los productos (bulto, hojas, lápices y clips). Están en el grupo de recursos **Ilustraciones**.
- Sin fotografías: los productos se muestran con su ilustración para que se lean igual en cualquier pantalla.

## Voz

Frases cortas en español, verbos en infinitivo para acciones («Escanear bulto», «Registrar salida»), sin tecnicismos. Los folios siempre con su prefijo: `OC-`, `FAC-`, `B-`, `T-`, `EMB-`.

## Usar los componentes

Las vistas previas cargan `components/bundle.css` (marcos Android y web, botones, chips, campos, barras, tablas) y `components/bundle.js` (`window.Cedis`: íconos, rutas de ilustraciones, catálogo de ejemplo, regla de zona por peso, generador de QR de muestra y avisos). Son vistas de referencia con datos de ejemplo; el QR es ilustrativo, no codifica datos reales.
