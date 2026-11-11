"""Lectura y escritura del Excel de stock.

Usamos openpyxl directamente (y no pandas.to_excel) para reescribir solo los
datos de cada hoja y conservar el formato que el cliente haya dado al libro.
"""

from pathlib import Path

import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill

HOJAS = {
    "Productos": ["ref_interna", "descripcion", "stock", "stock_minimo", "proveedor"],
    "Movimientos": ["fecha", "proveedor", "albaran", "ref_interna", "cantidad", "tipo"],
    "Equivalencias": ["proveedor", "ref_proveedor", "ref_interna", "unidades_por_bulto"],
    "Pendiente": [
        "fecha", "proveedor", "albaran", "ref_proveedor", "descripcion",
        "ref_interna", "unidades", "estado", "sugerencia", "confirmar",
    ],
    "Alertas": ["ref_interna", "descripcion", "stock", "stock_minimo", "cantidad_sugerida", "proveedor"],
}


def abrir(ruta: Path):
    try:
        return load_workbook(ruta)
    except FileNotFoundError:
        raise SystemExit(f"No existe {ruta}. Ejecuta antes: python scripts/generar_ejemplos.py")


def guardar(libro, ruta: Path) -> None:
    try:
        libro.save(ruta)
    except PermissionError:
        raise SystemExit(f"No puedo guardar {ruta}: ciérralo en Excel y vuelve a intentarlo.")


def leer_hoja(libro, nombre: str) -> pd.DataFrame:
    filas = list(libro[nombre].iter_rows(values_only=True))
    if not filas:
        return pd.DataFrame(columns=HOJAS[nombre])
    df = pd.DataFrame(filas[1:], columns=filas[0])
    df = df.dropna(how="all")
    # Las celdas vacías llegan como None; las dejamos como texto vacío.
    return df.astype(object).where(df.notna(), "")


def escribir_hoja(libro, nombre: str, df: pd.DataFrame) -> None:
    """Borra los datos (no el encabezado) y escribe el DataFrame."""
    hoja = libro[nombre]
    if hoja.max_row > 1:
        hoja.delete_rows(2, hoja.max_row - 1)
    for fila in df[HOJAS[nombre]].itertuples(index=False):
        hoja.append([None if v == "" else v for v in fila])


def crear_libro(ruta: Path, datos: dict[str, list[list]]) -> None:
    """Crea un Excel nuevo con las 5 hojas y encabezados con formato."""
    libro = Workbook()
    libro.remove(libro.active)
    for nombre, columnas in HOJAS.items():
        hoja = libro.create_sheet(nombre)
        hoja.append(columnas)
        for celda in hoja[1]:
            celda.font = Font(bold=True)
            celda.fill = PatternFill("solid", fgColor="DDEBF7")
        for fila in datos.get(nombre, []):
            hoja.append(fila)
        for letra, columna in zip("ABCDEFGHIJ", columnas):
            hoja.column_dimensions[letra].width = max(14, len(columna) + 4)
        hoja.freeze_panes = "A2"
    libro.save(ruta)
