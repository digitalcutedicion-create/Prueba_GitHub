"""
generar_mesas_json.py
Programa principal del generador de mesas.
"""

from pathlib import Path
from openpyxl import load_workbook

from parser_excel import leer_hoja
from exportador_json import exportar_json

BASE = Path(__file__).resolve().parent
EXCEL = BASE / "FINALES AGOSTO 2026.xlsx"
SALIDA = BASE.parent / "data" / "mesas.json"


def generar():
    if not EXCEL.exists():
        raise FileNotFoundError(f"No se encontró el Excel: {EXCEL}")

    print("=" * 50)
    print("GENERADOR DE MESAS FINALES")
    print("=" * 50)

    wb = load_workbook(EXCEL, data_only=True)

    registros = []

    for hoja in wb.worksheets:
        mesas = leer_hoja(hoja)
        registros.extend(mesas)
        print(f"- {hoja.title}: {len(mesas)} mesas")

    exportar_json(registros, SALIDA)

    print("-" * 50)
    print(f"Total de mesas: {len(registros)}")
    print(f"Archivo generado: {SALIDA}")
    print("Proceso finalizado correctamente.")


if __name__ == "__main__":
    generar()