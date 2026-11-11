"""Paso 2: traducir la referencia del proveedor a la referencia interna.

Cada proveedor llama a la misma pieza de forma distinta. La hoja
"Equivalencias" del Excel dice que, por ejemplo, la "RN-FA-220" de Recambios
Norte es nuestro "FIL-ACE-01", y que viene en cajas de 10 unidades.
"""

import difflib

import pandas as pd

OK = "OK"
DESCONOCIDA = "REF DESCONOCIDA"


def traducir(lineas: pd.DataFrame, proveedor: str, equivalencias: pd.DataFrame) -> pd.DataFrame:
    """Añade a cada línea: ref_interna, unidades, estado y sugerencia."""
    del_proveedor = equivalencias[equivalencias["proveedor"] == proveedor]
    tabla = {
        str(fila.ref_proveedor): (fila.ref_interna, fila.unidades_por_bulto)
        for fila in del_proveedor.itertuples()
    }
    conocidas = list(tabla)

    resultado = lineas.copy()
    refs_internas, unidades, estados, sugerencias = [], [], [], []
    for fila in lineas.itertuples():
        if fila.ref_proveedor in tabla:
            ref_interna, por_bulto = tabla[fila.ref_proveedor]
            refs_internas.append(ref_interna)
            unidades.append(fila.cantidad * por_bulto)  # cajas -> unidades
            estados.append(OK)
            sugerencias.append("")
        else:
            # No la conocemos: no inventamos nada, la marcamos para revisión
            # y proponemos la referencia más parecida como ayuda.
            parecidas = difflib.get_close_matches(fila.ref_proveedor, conocidas, n=1, cutoff=0.6)
            refs_internas.append("")
            unidades.append(fila.cantidad)
            estados.append(DESCONOCIDA)
            sugerencias.append(f"¿{parecidas[0]} ({tabla[parecidas[0]][0]})?" if parecidas else "")

    resultado["ref_interna"] = refs_internas
    resultado["unidades"] = unidades
    resultado["estado"] = estados
    resultado["sugerencia"] = sugerencias
    return resultado
