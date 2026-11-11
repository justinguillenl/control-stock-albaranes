"""Tests del flujo completo con datos ficticios. Ejecuta: python -m pytest"""

import shutil
import sys
from pathlib import Path

import pandas as pd
import pytest
from openpyxl import load_workbook

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from generar_ejemplos import EQUIVALENCIAS, PRODUCTOS, crear_albaran  # noqa: E402
from stock_albaranes import procesar  # noqa: E402
from stock_albaranes.equivalencias import DESCONOCIDA, traducir  # noqa: E402
from stock_albaranes.excel import crear_libro  # noqa: E402
from stock_albaranes.extraer import a_numero, extraer_albaran  # noqa: E402

CONFIG = RAIZ / "config" / "proveedores.json"


@pytest.fixture
def entorno(tmp_path):
    entrada, procesados, stock = tmp_path / "entrada", tmp_path / "procesados", tmp_path / "stock.xlsx"
    entrada.mkdir()
    crear_libro(stock, {"Productos": PRODUCTOS, "Equivalencias": EQUIVALENCIAS})
    crear_albaran(entrada / "a.pdf", "AN-1", "01/11/2026", [["RN-FA-220", "Filtro", 2, 38.5]])
    return entrada, procesados, stock


def test_a_numero():
    assert a_numero("1.234,50") == 1234.5
    assert a_numero("12,5 €") == 12.5
    assert a_numero("3") == 3


def test_extraer_albaran(entorno):
    entrada, _, _ = entorno
    alb = extraer_albaran(entrada / "a.pdf", procesar.cargar_config(CONFIG))
    assert alb["numero"] == "AN-1"
    assert alb["fecha"] == "01/11/2026"
    assert alb["lineas"].loc[0, "ref_proveedor"] == "RN-FA-220"
    assert alb["lineas"].loc[0, "cantidad"] == 2


def test_referencia_desconocida_se_marca_y_sugiere():
    equiv = pd.DataFrame(EQUIVALENCIAS, columns=["proveedor", "ref_proveedor", "ref_interna", "unidades_por_bulto"])
    lineas = pd.DataFrame([{"ref_proveedor": "RN-BI-045", "descripcion": "", "cantidad": 3, "precio": 1}])
    r = traducir(lineas, "RECAMBIOS_NORTE", equiv)
    assert r.loc[0, "estado"] == DESCONOCIDA
    assert r.loc[0, "ref_interna"] == ""
    assert "RN-BI-044" in r.loc[0, "sugerencia"]


def test_cajas_se_convierten_en_unidades():
    equiv = pd.DataFrame(EQUIVALENCIAS, columns=["proveedor", "ref_proveedor", "ref_interna", "unidades_por_bulto"])
    lineas = pd.DataFrame([{"ref_proveedor": "RN-FA-220", "descripcion": "", "cantidad": 2, "precio": 1}])
    assert traducir(lineas, "RECAMBIOS_NORTE", equiv).loc[0, "unidades"] == 20


def test_duplicado_no_entra_dos_veces(entorno):
    entrada, procesados, stock = entorno
    shutil.copy(entrada / "a.pdf", entrada / "b.pdf")
    informe = procesar.leer(entrada, procesados, stock, CONFIG)
    assert any(linea.startswith("DUPLICADO") for linea in informe)
    assert load_workbook(stock)["Pendiente"].max_row == 2  # encabezado + 1 línea


def test_stock_solo_cambia_tras_confirmar(entorno):
    entrada, procesados, stock = entorno
    procesar.leer(entrada, procesados, stock, CONFIG)

    procesar.aplicar(stock)  # sin confirmar: no cambia nada
    assert load_workbook(stock)["Productos"]["C2"].value == 12

    libro = load_workbook(stock)
    libro["Pendiente"]["J2"] = "sí"
    libro.save(stock)
    procesar.aplicar(stock)

    libro = load_workbook(stock)
    assert libro["Productos"]["C2"].value == 12 + 20
    assert libro["Pendiente"].max_row == 1
    assert libro["Movimientos"].max_row == 2
