"""Etiquetas QR de bultos en PDF (BE-24, R-06, A-10).

La etiqueta reproduce la vista del prototipo (`Proveedor/preview.html` · `.lab`): borde punteado
`#b9c6de` con esquinas redondeadas, QR a la izquierda y, a la derecha, «Bulto», «OC · Sucursal»
y «SKU · Piezas», con la etiqueta del dato en gris (`--ink-muted`) y el valor en seminegrita
(`--ink`), en Poppins. Las fuentes salen de `front/src/assets/fonts/` (licencia OFL).
"""

from dataclasses import dataclass
from pathlib import Path

import segno
from fpdf import FPDF

FUENTES = Path(__file__).parent / "fuentes"
INK = (0x0F, 0x1F, 0x3D)
INK_MUTED = (0x5B, 0x6B, 0x86)
BORDE = (0xB9, 0xC6, 0xDE)

# Medidas en mm. Carta para la impresora láser: 3 columnas por 7 filas = 21 etiquetas por hoja.
ANCHO, ALTO = 63.0, 32.0
SEPARACION = 3.0
MARGEN_X, MARGEN_Y = (215.9 - 3 * ANCHO - 2 * SEPARACION) / 2, 12.0
COLUMNAS, FILAS = 3, 7
QR_MM = 24.0


@dataclass(frozen=True)
class Etiqueta:
    bulto: str
    oc: str
    sucursal: str  # «Suc. 07», como el prototipo
    sku: str
    piezas: int
    qr: str  # texto que codifica el QR


def qr_svg(texto: str) -> bytes:
    """QR real en SVG, con el color de texto del prototipo."""
    import io

    salida = io.BytesIO()
    segno.make(texto, error="m").save(salida, kind="svg", scale=4, border=2, dark="#0f1f3d")
    return salida.getvalue()


def _pdf(formato: tuple[float, float] | str) -> FPDF:
    pdf = FPDF(unit="mm", format=formato)
    pdf.set_auto_page_break(False)
    pdf.add_font("Poppins", "", str(FUENTES / "Poppins-Regular.ttf"))
    pdf.add_font("Poppins", "B", str(FUENTES / "Poppins-SemiBold.ttf"))
    pdf.set_creator("CEDIS Flow")
    return pdf


def _dibujar(pdf: FPDF, e: Etiqueta, x: float, y: float) -> None:
    pdf.set_draw_color(*BORDE)
    pdf.set_line_width(0.4)
    pdf.set_dash_pattern(dash=1.2, gap=0.9)
    pdf.rect(x, y, ANCHO, ALTO, style="D", round_corners=True, corner_radius=3.5)
    pdf.set_dash_pattern()

    # QR: cada módulo es un cuadro relleno; así es nítido a cualquier escala.
    matriz = segno.make(e.qr, error="m").matrix
    n = len(matriz)
    modulo = QR_MM / n
    qx, qy = x + 3.5, y + (ALTO - QR_MM) / 2
    pdf.set_fill_color(*INK)
    for fila, valores in enumerate(matriz):
        for col, oscuro in enumerate(valores):
            if oscuro:
                pdf.rect(qx + col * modulo, qy + fila * modulo, modulo, modulo, style="F")

    tx, ty = qx + QR_MM + 3.5, y + 4.2
    ancho_texto = x + ANCHO - tx - 2.5
    for k, v in (
        ("Bulto", e.bulto),
        ("OC · Sucursal", f"{e.oc} · {e.sucursal}"),
        ("SKU · Piezas", f"{e.sku} · {e.piezas}"),
    ):
        pdf.set_xy(tx, ty)
        pdf.set_font("Poppins", "", 6.5)
        pdf.set_text_color(*INK_MUTED)
        pdf.cell(ancho_texto, 3.2, k)
        pdf.set_xy(tx, ty + 3.2)
        pdf.set_font("Poppins", "B", 8)
        pdf.set_text_color(*INK)
        pdf.cell(ancho_texto, 4, v)
        ty += 8.2


def etiqueta_pdf(e: Etiqueta) -> bytes:
    """Una sola etiqueta, en una hoja del tamaño de la etiqueta."""
    pdf = _pdf((ANCHO + 4, ALTO + 4))
    pdf.add_page()
    _dibujar(pdf, e, 2, 2)
    return bytes(pdf.output())


def etiquetas_pdf(etiquetas: list[Etiqueta]) -> bytes:
    """Todas las etiquetas en hojas carta, 21 por hoja."""
    pdf = _pdf("Letter")
    por_hoja = COLUMNAS * FILAS
    for i, e in enumerate(etiquetas):
        if i % por_hoja == 0:
            pdf.add_page()
        lugar = i % por_hoja
        col, fila = lugar % COLUMNAS, lugar // COLUMNAS
        _dibujar(
            pdf,
            e,
            MARGEN_X + col * (ANCHO + SEPARACION),
            MARGEN_Y + fila * (ALTO + SEPARACION),
        )
    return bytes(pdf.output())
