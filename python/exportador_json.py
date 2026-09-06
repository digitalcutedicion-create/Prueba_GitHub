"""
exportador_json.py
Exporta la lista de mesas a un archivo JSON UTF-8.
"""

from pathlib import Path
import json


def exportar_json(registros, destino):
    """
    registros: lista de diccionarios
    destino: ruta del archivo json
    """

    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)

    with destino.open("w", encoding="utf-8") as archivo:
        json.dump(
            registros,
            archivo,
            ensure_ascii=False,
            indent=2
        )

    return destino


if __name__ == "__main__":
    # Prueba rápida
    ejemplo = [
        {
            "carrera": "Diseño Gráfico",
            "anio": "1",
            "division": "A",
            "turno": "Mañana",
            "dia": "2026-08-03",
            "hora": "08:00",
            "materia": "Diseño I",
            "presidente": "Prof. Pérez",
            "vocal1": "Prof. Gómez",
            "vocal2": "Prof. López"
        }
    ]

    salida = exportar_json(ejemplo, "../data/mesas.json")
    print(f"JSON generado en: {salida}")
