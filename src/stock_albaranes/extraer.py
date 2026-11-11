"""Paso 1 del flujo: leer un albarán en PDF y sacar sus datos.

Devuelve el proveedor, el número de albarán, la fecha y una tabla (DataFrame)
con una fila por línea del albarán.

Solo funciona con PDFs *digitales* (los que tienen texto seleccionable).
Los escaneados o fotografiados necesitan reconocimiento de texto (versión 3).
"""

import re
from pathlib import Path

import pandas as pd
import pdfplumber


class ErrorAlbaran(Exception):
    """Algo en el PDF no tiene el formato esperado."""


def leer_pdf(ruta: Path) -> tuple[str, list[list[str]]]:
    """Devuelve todo el texto del PDF y las filas de todas sus tablas."""
    texto = ""
    filas: list[list[str]] = []
    with pdfplumber.open(ruta) as pdf:
        for pagina in pdf.pages:
            texto += (pagina.extract_text() or "") + "\n"
            for tabla in pagina.extract_tables():
                filas.extend(tabla)
    return texto, filas


def detectar_proveedor(texto: str, config: dict) -> str:
    """Busca en el texto qué proveedor de la configuración emitió el albarán."""
    for clave, datos in config.items():
        if datos["detectar"].lower() in texto.lower():
            return clave
    raise ErrorAlbaran("Proveedor no reconocido: añádelo a config/proveedores.json")


def buscar(patron: str, texto: str, que: str) -> str:
    coincidencia = re.search(patron, texto)
    if not coincidencia:
        raise ErrorAlbaran(f"No encuentro el {que} en el albarán")
    return coincidencia.group(1)


def a_numero(valor) -> float:
    """Convierte '1.234,50' o '12,5' o '3' en número."""
    texto = str(valor).strip().replace("€", "").replace(" ", "")
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    return float(texto)


def filas_a_tabla(filas: list[list[str]], columnas: dict) -> pd.DataFrame:
    """Convierte las filas crudas del PDF en una tabla limpia.

    `columnas` traduce los encabezados del proveedor a nuestros nombres,
    por ejemplo {"Referencia": "ref_proveedor"}.
    """
    # Buscamos la fila de encabezados: la que contiene todos los nombres esperados.
    esperados = set(columnas)
    inicio = None
    for i, fila in enumerate(filas):
        celdas = {str(c).strip() for c in fila if c}
        if esperados <= celdas:
            inicio = i
            break
    if inicio is None:
        raise ErrorAlbaran(f"No encuentro una tabla con las columnas {sorted(esperados)}")

    encabezado = [str(c).strip() if c else "" for c in filas[inicio]]
    df = pd.DataFrame(filas[inicio + 1 :], columns=encabezado)
    df = df[list(columnas)].rename(columns=columnas)

    # Limpieza: quitamos filas vacías o de totales (sin referencia).
    df["ref_proveedor"] = df["ref_proveedor"].fillna("").astype(str).str.strip()
    df = df[df["ref_proveedor"] != ""]
    df["descripcion"] = df["descripcion"].fillna("").astype(str).str.strip()
    df["cantidad"] = df["cantidad"].map(a_numero)
    df["precio"] = df["precio"].map(a_numero)
    return df.reset_index(drop=True)


def extraer_albaran(ruta: Path, config: dict) -> dict:
    """Función principal de este módulo: PDF -> datos del albarán."""
    texto, filas = leer_pdf(ruta)
    proveedor = detectar_proveedor(texto, config)
    datos = config[proveedor]
    return {
        "proveedor": proveedor,
        "numero": buscar(datos["patron_numero"], texto, "número de albarán"),
        "fecha": buscar(datos["patron_fecha"], texto, "fecha"),
        "lineas": filas_a_tabla(filas, datos["columnas"]),
    }
