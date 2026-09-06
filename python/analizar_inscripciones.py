# -*- coding: utf-8 -*-
"""
Analiza las inscripciones individuales para determinar la cantidad de
inscriptos por mesa, sin modificar el portal.

REGLA DE SEGURIDAD:
- Cada fila de las hojas de carrera cuenta como 1 inscripción.
- NO se usa TOTAL GENERAL ni MESAS A ARMAR para contar.
- Se agrupan las inscripciones por Carrera + Materia + Turno.
- Solo se asigna un número si existe UNA ÚNICA mesa con conInscriptos=true
  para esa combinación.
- Si hay cero o varias mesas posibles, NO se asigna ningún número.
- data/mesas.json NO se modifica.
"""

from pathlib import Path
from collections import Counter, defaultdict
import json
import re
import unicodedata
import openpyxl


EXCEL_NAME = "listado_finales_Mesas_Agosto_2026_V2.xlsx"
JSON_NAME = "mesas.json"

HOJAS_NO_INDIVIDUALES = {"TOTAL GENERAL", "MESAS A ARMAR"}


def normalizar(texto):
    if texto is None:
        return ""

    texto = str(texto).strip().lower()

    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(
        c for c in texto if unicodedata.category(c) != "Mn"
    )

    # Unificar ordinales y algunos signos que no aportan a la identidad.
    texto = texto.replace("º", " ")
    texto = texto.replace("°", " ")

    # El Excel puede tener pequeñas diferencias de puntuación/espacios.
    texto = re.sub(r"[.,;:/_\-]+", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()

    return texto


def normalizar_carrera(carrera):
    c = normalizar(carrera)

    equivalencias = {
        "medios": "artes y medios audiovisuales",
        "artes y medios audiovisuales": "artes y medios audiovisuales",
        "profesorado": "profesorado en artes visuales",
        "profesorado en artes visuales": "profesorado en artes visuales",
        "foba esceno": "escenografia",
        "foba escenografia": "escenografia",
        "escenografia": "escenografia",
        "foba av": "artes y medios audiovisuales",
    }

    return equivalencias.get(c, c)


def normalizar_turno(turno):
    return normalizar(turno)


def clave_mesa(mesa):
    return (
        normalizar_carrera(mesa.get("carrera")),
        normalizar(mesa.get("materia")),
        normalizar_turno(mesa.get("turno")),
    )


def main():
    carpeta_python = Path(__file__).resolve().parent
    raiz = carpeta_python.parent

    excel_path = carpeta_python / EXCEL_NAME
    json_path = raiz / "data" / JSON_NAME

    if not excel_path.exists():
        raise FileNotFoundError(
            f"No se encontró el Excel:\n{excel_path}"
        )

    if not json_path.exists():
        raise FileNotFoundError(
            f"No se encontró mesas.json:\n{json_path}"
        )

    print("=" * 70)
    print("ANÁLISIS DE INSCRIPCIONES INDIVIDUALES — MODO SEGURO")
    print("=" * 70)
    print(f"Excel: {excel_path.name}")
    print(f"JSON:  {json_path}")
    print()

    # ------------------------------------------------------------
    # 1. Leer mesas actuales
    # ------------------------------------------------------------
    with json_path.open("r", encoding="utf-8") as f:
        mesas = json.load(f)

    print(f"Mesas en mesas.json: {len(mesas)}")

    mesas_con_inscriptos = defaultdict(list)

    for indice, mesa in enumerate(mesas):
        if mesa.get("conInscriptos") is True:
            mesas_con_inscriptos[clave_mesa(mesa)].append(indice)

    total_mesas_con_inscriptos = sum(
        1 for m in mesas if m.get("conInscriptos") is True
    )

    print(f"Mesas con conInscriptos=true: {total_mesas_con_inscriptos}")
    print()

    # ------------------------------------------------------------
    # 2. Leer SOLO hojas con inscripciones individuales
    # ------------------------------------------------------------
    wb = openpyxl.load_workbook(
        excel_path,
        data_only=True,
        read_only=True,
    )

    print("Hojas utilizadas:")
    hojas_utilizadas = []

    inscripciones_por_clave = Counter()
    filas_por_hoja = Counter()

    for ws in wb.worksheets:
        if ws.title in HOJAS_NO_INDIVIDUALES:
            continue

        # Encabezado esperado en fila 1:
        # Carrera, Materia, DNI, ..., Turno, Curso Actual,
        # Curso de la UC Adeudada, ...
        filas_hoja = 0

        for fila in ws.iter_rows(min_row=2, values_only=True):
            if not any(valor is not None for valor in fila):
                continue

            valores = list(fila) + [None] * 10

            carrera = valores[0]
            materia = valores[1]
            turno = valores[6]

            # Una fila válida de inscripción necesita al menos
            # carrera, materia y turno.
            if not carrera or not materia or not turno:
                continue

            clave = (
                normalizar_carrera(carrera),
                normalizar(materia),
                normalizar_turno(turno),
            )

            inscripciones_por_clave[clave] += 1
            filas_hoja += 1

        if filas_hoja:
            hojas_utilizadas.append((ws.title, filas_hoja))
            filas_por_hoja[ws.title] = filas_hoja

    for nombre, cantidad in hojas_utilizadas:
        print(f"  - {nombre}: {cantidad} inscripciones")

    print()
    print(f"Inscripciones individuales contadas: {sum(inscripciones_por_clave.values())}")
    print(f"Combinaciones Carrera+Materia+Turno: {len(inscripciones_por_clave)}")
    print()

    # ------------------------------------------------------------
    # 3. Determinar asignaciones seguras
    # ------------------------------------------------------------
    asignaciones = {}
    ambiguas = []
    sin_mesa = []

    for clave, cantidad in sorted(inscripciones_por_clave.items()):
        candidatos = mesas_con_inscriptos.get(clave, [])

        if len(candidatos) == 1:
            indice = candidatos[0]
            asignaciones[indice] = cantidad

        elif len(candidatos) > 1:
            ambiguas.append((clave, cantidad, candidatos))

        else:
            sin_mesa.append((clave, cantidad))

    print("=" * 70)
    print("RESULTADO")
    print("=" * 70)
    print(f"MESAS CON CANTIDAD ASIGNABLE: {len(asignaciones)}")
    print(f"COMBINACIONES AMBIGUAS:       {len(ambiguas)}")
    print(f"SIN MESA CON INSCRIPTOS:      {len(sin_mesa)}")
    print()

    # ------------------------------------------------------------
    # 4. Crear JSON de prueba SIN tocar el original
    # ------------------------------------------------------------
    salida_json = raiz / "data" / "mesas_con_cantidad_individuales.json"

    mesas_prueba = []

    for indice, mesa_original in enumerate(mesas):
        mesa = dict(mesa_original)

        if indice in asignaciones:
            mesa["cantidadInscriptos"] = asignaciones[indice]

        mesas_prueba.append(mesa)

    with salida_json.open("w", encoding="utf-8") as f:
        json.dump(
            mesas_prueba,
            f,
            ensure_ascii=False,
            indent=2,
        )

    # ------------------------------------------------------------
    # 5. Reporte
    # ------------------------------------------------------------
    reporte = raiz / "python" / "reporte_inscripciones_individuales.txt"

    with reporte.open("w", encoding="utf-8") as f:
        f.write("REPORTE — INSCRIPCIONES INDIVIDUALES\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Excel: {excel_path.name}\n")
        f.write(f"Mesas originales: {len(mesas)}\n")
        f.write(f"Mesas con conInscriptos=true: {total_mesas_con_inscriptos}\n")
        f.write(
            f"Mesas con cantidad asignada: {len(asignaciones)}\n"
        )
        f.write(
            f"Combinaciones ambiguas: {len(ambiguas)}\n"
        )
        f.write(
            f"Combinaciones sin mesa con inscriptos: {len(sin_mesa)}\n\n"
        )

        f.write("REGLA UTILIZADA\n")
        f.write("-" * 70 + "\n")
        f.write(
            "Cada fila de las hojas individuales cuenta como 1 inscripción.\n"
        )
        f.write(
            "Se excluyen TOTAL GENERAL y MESAS A ARMAR para evitar duplicar.\n"
        )
        f.write(
            "Solo se asigna cantidad cuando existe una única mesa "
            "con conInscriptos=true.\n"
        )
        f.write(
            "Los casos ambiguos o sin mesa quedan SIN número.\n\n"
        )

        f.write("HOJAS UTILIZADAS\n")
        f.write("-" * 70 + "\n")
        for nombre, cantidad in hojas_utilizadas:
            f.write(f"{nombre}: {cantidad}\n")

        f.write("\nASIGNACIONES\n")
        f.write("-" * 70 + "\n")
        for indice in sorted(asignaciones):
            mesa = mesas[indice]
            f.write(
                f"MESA {indice}: "
                f"{mesa.get('carrera')} | "
                f"{mesa.get('materia')} | "
                f"{mesa.get('turno')} | "
                f"{mesa.get('anio')} {mesa.get('division')} | "
                f"CANTIDAD={asignaciones[indice]}\n"
            )

        f.write("\nCASOS AMBIGUOS — SIN NÚMERO\n")
        f.write("-" * 70 + "\n")
        for clave, cantidad, candidatos in ambiguas:
            f.write(
                f"{clave} | cantidad={cantidad} | "
                f"candidatos={candidatos}\n"
            )

        f.write("\nCASOS SIN MESA CON INSCRIPTOS — SIN NÚMERO\n")
        f.write("-" * 70 + "\n")
        for clave, cantidad in sin_mesa:
            f.write(f"{clave} | cantidad={cantidad}\n")

        f.write("\nVALIDACIÓN\n")
        f.write("-" * 70 + "\n")
        f.write(
            "OK — mesas.json original NO fue modificado.\n"
        )

    print("Archivos generados:")
    print(f"  {salida_json}")
    print(f"  {reporte}")
    print()
    print("IMPORTANTE:")
    print("data/mesas.json NO fue modificado.")
    print("Los casos ambiguos o no identificados quedan sin número.")


if __name__ == "__main__":
    main()
