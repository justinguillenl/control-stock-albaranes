"""Genera datos ficticios para probar la herramienta.

- data/stock.xlsx con productos, equivalencias y hojas vacías.
- 3 albaranes PDF de un proveedor inventado en data/entrada:
    * uno normal (con productos que vienen en cajas),
    * uno con una referencia que no está en Equivalencias,
    * una copia del primero con otro nombre de archivo (debe detectarse como duplicado).

Ningún dato es real: así puedes publicar el repositorio sin problemas.
"""

import shutil
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from stock_albaranes.excel import crear_libro  # noqa: E402

PRODUCTOS = [
    ["FIL-ACE-01", "Filtro de aceite turismo", 12, 10, "RECAMBIOS_NORTE"],
    ["FIL-AIR-02", "Filtro de aire turismo", 4, 8, "RECAMBIOS_NORTE"],
    ["PAS-FRE-01", "Pastillas de freno delanteras", 6, 6, "RECAMBIOS_NORTE"],
    ["BUJ-IRI-01", "Bujía de iridio", 30, 20, "RECAMBIOS_NORTE"],
    ["ACE-5W30-5", "Aceite 5W30 5 L", 3, 5, "RECAMBIOS_NORTE"],
    ["ESC-LIM-55", "Escobilla limpiaparabrisas 55 cm", 9, 6, "RECAMBIOS_NORTE"],
]

EQUIVALENCIAS = [
    ["RECAMBIOS_NORTE", "RN-FA-220", "FIL-ACE-01", 10],
    ["RECAMBIOS_NORTE", "RN-FR-115", "FIL-AIR-02", 1],
    ["RECAMBIOS_NORTE", "RN-PF-301", "PAS-FRE-01", 1],
    ["RECAMBIOS_NORTE", "RN-BI-044", "BUJ-IRI-01", 4],
    ["RECAMBIOS_NORTE", "RN-AC-530", "ACE-5W30-5", 1],
    ["RECAMBIOS_NORTE", "RN-EL-055", "ESC-LIM-55", 2],
]


def crear_albaran(ruta: Path, numero: str, fecha: str, lineas: list[list]) -> None:
    estilos = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(ruta), pagesize=A4)
    tabla = [["Referencia", "Descripción", "Cantidad", "Precio"]] + [
        [ref, desc, str(cant), f"{precio:.2f}".replace(".", ",")] for ref, desc, cant, precio in lineas
    ]
    t = Table(tabla, colWidths=[90, 230, 70, 70])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
    ]))
    doc.build([
        Paragraph("Recambios Norte S.L. · CIF B00000000 (ficticio)", estilos["Title"]),
        Paragraph(f"Albarán nº: {numero}", estilos["Normal"]),
        Paragraph(f"Fecha: {fecha}", estilos["Normal"]),
        Spacer(1, 16),
        t,
    ])


def main() -> None:
    datos = RAIZ / "data"
    entrada = datos / "entrada"
    entrada.mkdir(parents=True, exist_ok=True)

    crear_libro(datos / "stock.xlsx", {"Productos": PRODUCTOS, "Equivalencias": EQUIVALENCIAS})

    a1 = entrada / "albaran_AN-2026-0153.pdf"
    crear_albaran(a1, "AN-2026-0153", "03/11/2026", [
        ["RN-FA-220", "Filtro aceite (caja 10 uds)", 2, 38.50],
        ["RN-FR-115", "Filtro aire", 6, 7.90],
        ["RN-AC-530", "Aceite 5W30 5L", 4, 24.00],
    ])
    crear_albaran(entrada / "albaran_AN-2026-0154.pdf", "AN-2026-0154", "05/11/2026", [
        ["RN-PF-301", "Pastillas freno del.", 4, 18.20],
        ["RN-BI-045", "Bujía iridio (blíster 4)", 3, 29.60],
        ["RN-EL-055", "Escobilla 55 cm (pack 2)", 2, 11.40],
    ])
    shutil.copy(a1, entrada / "copia_reenviada_por_email.pdf")

    print("Creados data/stock.xlsx y 3 albaranes en data/entrada")


if __name__ == "__main__":
    main()
