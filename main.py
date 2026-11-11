"""Punto de entrada.

Uso:
    python main.py leer      # lee los PDFs de data/entrada y los deja en "Pendiente"
    python main.py aplicar   # aplica al stock las líneas con "sí" en "confirmar"
"""

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "src"))

from stock_albaranes import procesar  # noqa: E402

ENTRADA = RAIZ / "data" / "entrada"
PROCESADOS = RAIZ / "data" / "procesados"
STOCK = RAIZ / "data" / "stock.xlsx"
CONFIG = RAIZ / "config" / "proveedores.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Control de stock desde albaranes en PDF")
    parser.add_argument("orden", choices=["leer", "aplicar"])
    args = parser.parse_args()

    if args.orden == "leer":
        informe = procesar.leer(ENTRADA, PROCESADOS, STOCK, CONFIG)
        informe.append("\nRevisa la hoja 'Pendiente' de data/stock.xlsx, escribe 'sí' en"
                       " 'confirmar' y ejecuta: python main.py aplicar")
    else:
        informe = procesar.aplicar(STOCK)

    print("\n".join(informe))


if __name__ == "__main__":
    main()
