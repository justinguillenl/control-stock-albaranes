"""Las dos órdenes de la herramienta.

1. leer():   PDFs de data/entrada  ->  hoja "Pendiente" (sin tocar el stock)
2. aplicar(): filas confirmadas de "Pendiente"  ->  Productos + Movimientos + Alertas

Separarlas es deliberado: el stock solo cambia cuando una persona ha revisado
y escrito "sí" en la columna "confirmar".
"""

import json
import shutil
from pathlib import Path

import pandas as pd

from . import excel
from .equivalencias import traducir
from .extraer import ErrorAlbaran, extraer_albaran

CONFIRMADO = {"sí", "si", "x", "ok"}


def cargar_config(ruta: Path) -> dict:
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def mover(pdf: Path, carpeta: Path) -> None:
    carpeta.mkdir(parents=True, exist_ok=True)
    shutil.move(str(pdf), carpeta / pdf.name)


def leer(entrada: Path, procesados: Path, ruta_stock: Path, ruta_config: Path) -> list[str]:
    config = cargar_config(ruta_config)
    libro = excel.abrir(ruta_stock)
    movimientos = excel.leer_hoja(libro, "Movimientos")
    pendiente = excel.leer_hoja(libro, "Pendiente")
    equivalencias = excel.leer_hoja(libro, "Equivalencias")

    # Albaranes ya vistos: aplicados (Movimientos) o en revisión (Pendiente).
    vistos = {
        (str(f.proveedor), str(f.albaran))
        for df in (movimientos, pendiente)
        for f in df.itertuples()
    }

    informe, nuevas = [], []
    for pdf in sorted(entrada.glob("*.pdf")):
        try:
            alb = extraer_albaran(pdf, config)
        except ErrorAlbaran as error:
            informe.append(f"ERROR     {pdf.name}: {error}")
            mover(pdf, procesados / "errores")
            continue

        clave = (alb["proveedor"], alb["numero"])
        if clave in vistos:
            informe.append(f"DUPLICADO {pdf.name}: el albarán {alb['numero']} ya estaba registrado")
            mover(pdf, procesados / "duplicados")
            continue
        vistos.add(clave)

        lineas = traducir(alb["lineas"], alb["proveedor"], equivalencias)
        lineas["fecha"] = alb["fecha"]
        lineas["proveedor"] = alb["proveedor"]
        lineas["albaran"] = alb["numero"]
        lineas["confirmar"] = ""
        nuevas.append(lineas)

        desconocidas = (lineas["estado"] != "OK").sum()
        aviso = f" ({desconocidas} referencias desconocidas)" if desconocidas else ""
        informe.append(f"LEÍDO     {pdf.name}: {len(lineas)} líneas{aviso}")
        mover(pdf, procesados)

    if nuevas:
        pendiente = pd.concat([pendiente, *nuevas], ignore_index=True)
        excel.escribir_hoja(libro, "Pendiente", pendiente)
        excel.guardar(libro, ruta_stock)
    if not informe:
        informe.append("No hay PDFs en la carpeta de entrada.")
    return informe


def aplicar(ruta_stock: Path) -> list[str]:
    libro = excel.abrir(ruta_stock)
    productos = excel.leer_hoja(libro, "Productos")
    movimientos = excel.leer_hoja(libro, "Movimientos")
    pendiente = excel.leer_hoja(libro, "Pendiente")

    productos = productos.set_index("ref_interna")
    informe, quedan, nuevos_mov = [], [], []

    for fila in pendiente.to_dict("records"):
        confirmada = str(fila["confirmar"]).strip().lower() in CONFIRMADO
        ref = str(fila["ref_interna"]).strip()
        if not confirmada:
            quedan.append(fila)
            continue
        if ref not in productos.index:
            fila["estado"] = "REF NO EXISTE EN PRODUCTOS"
            quedan.append(fila)
            informe.append(f"SIN APLICAR {fila['albaran']} {fila['ref_proveedor']}: ref_interna '{ref}' no existe")
            continue

        productos.loc[ref, "stock"] = productos.loc[ref, "stock"] + fila["unidades"]
        nuevos_mov.append({
            "fecha": fila["fecha"], "proveedor": fila["proveedor"], "albaran": fila["albaran"],
            "ref_interna": ref, "cantidad": fila["unidades"], "tipo": "entrada",
        })
        informe.append(f"APLICADO  {fila['albaran']} {ref}: +{fila['unidades']:g}")

    productos = productos.reset_index()
    movimientos = pd.concat([movimientos, pd.DataFrame(nuevos_mov)], ignore_index=True)
    pendiente = pd.DataFrame(quedan, columns=excel.HOJAS["Pendiente"])

    excel.escribir_hoja(libro, "Productos", productos)
    excel.escribir_hoja(libro, "Movimientos", movimientos)
    excel.escribir_hoja(libro, "Pendiente", pendiente)
    excel.escribir_hoja(libro, "Alertas", calcular_alertas(productos))
    excel.guardar(libro, ruta_stock)

    if not informe:
        informe.append("No había líneas confirmadas en 'Pendiente'.")
    return informe


def calcular_alertas(productos: pd.DataFrame) -> pd.DataFrame:
    """Productos por debajo del mínimo.

    Regla sencilla (ajústala con cada cliente): pedir hasta el doble del mínimo.
    """
    bajo = productos[productos["stock"] < productos["stock_minimo"]].copy()
    bajo["cantidad_sugerida"] = bajo["stock_minimo"] * 2 - bajo["stock"]
    return bajo
