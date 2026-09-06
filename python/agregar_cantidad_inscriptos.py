"""
Agrega cantidad de inscriptos al mesas.json SIN modificar los datos existentes.

Uso:
    Desde la raíz del proyecto:
        python python/agregar_cantidad_inscriptos.py

El script:
1. Lee python/listado_finales_Mesas_Agosto_2026_V2.xlsx, hoja MESAS A ARMAR.
2. Lee data/mesas.json.
3. Intenta asociar cada cantidad a una mesa de forma conservadora.
4. NO modifica data/mesas.json.
5. Genera:
      data/mesas_con_cantidad.json
      python/reporte_cantidad_inscriptos.txt

Regla principal:
- Solo agrega un número cuando la correspondencia es segura.
- Si no puede determinar la mesa, NO inventa el número.
- En esos casos se conserva únicamente conInscriptos: true.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections import defaultdict, Counter
from pathlib import Path

import pandas as pd


# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

EXCEL_PATH = SCRIPT_DIR / "listado_finales_Mesas_Agosto_2026_V2.xlsx"
JSON_PATH = PROJECT_ROOT / "data" / "mesas.json"

OUTPUT_JSON = PROJECT_ROOT / "data" / "mesas_con_cantidad.json"
REPORT_PATH = SCRIPT_DIR / "reporte_cantidad_inscriptos.txt"


# ---------------------------------------------------------------------------
# Normalización
# ---------------------------------------------------------------------------

def normalizar(texto) -> str:
    """Normaliza texto para comparar sin depender de mayúsculas/acentos."""
    if texto is None:
        return ""

    if pd.isna(texto):
        return ""

    texto = str(texto).strip()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(
        caracter for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )
    texto = texto.lower()
    texto = texto.replace("&", " y ")
    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def normalizar_carrera_excel(carrera: str) -> str:
    """
    Convierte los nombres abreviados del Excel al nombre que usa mesas.json.
    """
    clave = normalizar(carrera)

    equivalencias = {
        "diseno grafico": "Diseno Grafico",
        "escenografia": "Escenografia",
        "foba esceno": "Escenografia",
        "fotografia": "Fotografia",
        "ilustracion": "Ilustracion",
        "medios": "Artes Y Medios Audiovisuales",
        "profesorado": "Profesorado En Artes Visuales",
        "realizador": "Realizador",
    }

    return equivalencias.get(clave, str(carrera).strip())


def normalizar_turno(turno: str) -> str:
    clave = normalizar(turno)

    equivalencias = {
        "manana": "Manana",
        "tarde": "Tarde",
        "noche": "Noche",
    }

    return equivalencias.get(clave, str(turno).strip().title())


def separar_curso(curso):
    """
    Convierte:
        1a -> ("1", "A")
        2c -> ("2", "C")
        FOBA 8 -> ("0", "")
    """
    clave = normalizar(curso)

    if clave.startswith("foba"):
        return "0", ""

    match = re.fullmatch(r"(\d+)\s*([a-z])", clave)
    if match:
        return match.group(1), match.group(2).upper()

    return None, None


# ---------------------------------------------------------------------------
# Claves de comparación
# ---------------------------------------------------------------------------

def clave_mesa(mesa: dict) -> tuple:
    return (
        normalizar(mesa.get("carrera")),
        normalizar(mesa.get("materia")),
        normalizar(mesa.get("turno")),
        str(mesa.get("anio", "")).strip(),
        normalizar(mesa.get("division", "")),
    )


def clave_excel(fila: dict) -> tuple:
    anio, division = separar_curso(fila.get("Curso de la UC Adeudada"))

    return (
        normalizar(normalizar_carrera_excel(fila.get("Carrera"))),
        normalizar(fila.get("Materia")),
        normalizar(normalizar_turno(fila.get("Turno"))),
        str(anio or "").strip(),
        normalizar(division or ""),
    )


def clave_base_excel(fila: dict) -> tuple:
    return clave_excel(fila)[:3]


def clave_base_mesa(mesa: dict) -> tuple:
    return clave_mesa(mesa)[:3]


# ---------------------------------------------------------------------------
# Carga
# ---------------------------------------------------------------------------

def cargar_datos():
    if not EXCEL_PATH.exists():
        raise FileNotFoundError(
            f"No se encontró el Excel:\n{EXCEL_PATH}"
        )

    if not JSON_PATH.exists():
        raise FileNotFoundError(
            f"No se encontró el mesas.json:\n{JSON_PATH}"
        )

    df = pd.read_excel(EXCEL_PATH, sheet_name="MESAS A ARMAR")

    columnas_necesarias = {
        "Carrera",
        "Materia",
        "Turno",
        "Curso de la UC Adeudada",
        "Cantidad de inscriptos",
    }

    faltantes = columnas_necesarias - set(df.columns)
    if faltantes:
        raise ValueError(
            "Faltan columnas en 'MESAS A ARMAR': "
            + ", ".join(sorted(faltantes))
        )

    with JSON_PATH.open("r", encoding="utf-8") as archivo:
        mesas = json.load(archivo)

    if not isinstance(mesas, list):
        raise ValueError("mesas.json no contiene una lista de mesas.")

    return df, mesas


# ---------------------------------------------------------------------------
# Proceso conservador
# ---------------------------------------------------------------------------

def procesar(df, mesas):
    # Agrupamos por clave exacta de la UC adeudada.
    # Si hubiera más de una fila con la misma clave, se suman sus cantidades.
    cantidades = defaultdict(int)
    filas_por_clave = defaultdict(int)

    for _, fila in df.iterrows():
        try:
            cantidad = int(fila["Cantidad de inscriptos"])
        except (TypeError, ValueError):
            continue

        if cantidad < 0:
            continue

        clave = clave_excel(fila.to_dict())
        cantidades[clave] += cantidad
        filas_por_clave[clave] += 1

    # Índices de mesas.
    mesas_por_clave = defaultdict(list)
    mesas_por_base = defaultdict(list)

    for indice, mesa in enumerate(mesas):
        mesas_por_clave[clave_mesa(mesa)].append(indice)
        mesas_por_base[clave_base_mesa(mesa)].append(indice)

    # Copia profunda sencilla mediante JSON para no tocar el objeto original.
    resultado = json.loads(json.dumps(mesas, ensure_ascii=False))

    asignaciones = defaultdict(list)
    estados = Counter()
    detalles = []

    # Primera pasada: correspondencia exacta.
    claves_procesadas = sorted(cantidades.keys())

    for clave, cantidad in cantidades.items():
        candidatos = mesas_por_clave.get(clave, [])

        if len(candidatos) == 1:
            indice = candidatos[0]
            mesa = mesas[indice]

            if mesa.get("conInscriptos") is True:
                asignaciones[indice].append(
                    ("exacta", cantidad, clave)
                )
                estados["coincidencia_exacta"] += 1
            else:
                estados["exacta_pero_mesa_sin_inscriptos"] += 1
                detalles.append(
                    "NO ASIGNADA | coincidencia exacta, pero la mesa "
                    "tiene conInscriptos=false | "
                    f"clave={clave} | cantidad={cantidad}"
                )

        elif len(candidatos) == 0:
            estados["sin_coincidencia_exacta"] += 1
        else:
            estados["coincidencia_ambigua"] += 1
            detalles.append(
                "NO ASIGNADA | más de una mesa coincide exactamente | "
                f"clave={clave} | candidatos={candidatos} | "
                f"cantidad={cantidad}"
            )

    # Segunda pasada MUY conservadora:
    # si una combinación carrera+materia+turno no tiene coincidencia exacta,
    # pero existe UNA SOLA mesa con inscriptos para esa combinación, podemos
    # asociar la cantidad a esa mesa. Si hay más de una, no adivinamos.
    for clave, cantidad in cantidades.items():
        candidatos_exactos = mesas_por_clave.get(clave, [])

        if len(candidatos_exactos) == 1:
            continue
        if len(candidatos_exactos) > 1:
            continue

        base = clave[:3]
        candidatos_base = mesas_por_base.get(base, [])
        candidatos_con_inscriptos = [
            i for i in candidatos_base
            if mesas[i].get("conInscriptos") is True
        ]

        if len(candidatos_con_inscriptos) == 1:
            indice = candidatos_con_inscriptos[0]

            # Si ya recibió una asignación exacta, no usamos fallback.
            if asignaciones.get(indice):
                continue

            asignaciones[indice].append(
                ("única_mesa_con_inscriptos", cantidad, clave)
            )
            estados["asignacion_por_unica_mesa_con_inscriptos"] += 1

        elif len(candidatos_con_inscriptos) == 0:
            estados["sin_mesa_con_inscriptos_para_fallback"] += 1
            detalles.append(
                "NO ASIGNADA | no hay una única mesa con inscriptos | "
                f"clave={clave} | cantidad={cantidad}"
            )

        else:
            estados["fallback_ambiguo"] += 1
            detalles.append(
                "NO ASIGNADA | hay varias mesas con inscriptos "
                "para la misma carrera/materia/turno | "
                f"clave={clave} | candidatos={candidatos_con_inscriptos} | "
                f"cantidad={cantidad}"
            )

    # Escribimos cantidades solamente si una mesa recibió una única
    # asignación inequívoca. Si por cualquier motivo recibe varias fuentes,
    # NO sumamos: se considera ambiguo y queda sin número.
    asignadas_ok = 0
    asignadas_ambiguas = 0

    for indice, fuentes in asignaciones.items():
        if len(fuentes) != 1:
            asignadas_ambiguas += 1
            detalles.append(
                "NO ASIGNADA | una misma mesa recibió varias posibles "
                "fuentes de cantidad | "
                f"mesa={indice} | fuentes={fuentes}"
            )
            continue

        _, cantidad, clave = fuentes[0]

        # Protección adicional:
        # jamás ponemos cantidad en una mesa que actualmente no tenga
        # conInscriptos=true.
        if resultado[indice].get("conInscriptos") is not True:
            continue

        resultado[indice]["cantidadInscriptos"] = int(cantidad)
        asignadas_ok += 1

    # Todas las mesas sin número conservan exactamente su estado original.
    # No agregamos cantidadInscriptos=0.
    for indice, mesa_original in enumerate(mesas):
        if "cantidadInscriptos" not in resultado[indice]:
            resultado[indice].pop("cantidadInscriptos", None)

    return resultado, estados, detalles, asignadas_ok, asignadas_ambiguas


# ---------------------------------------------------------------------------
# Validación de integridad
# ---------------------------------------------------------------------------

def validar_integridad(original, resultado):
    errores = []

    if len(original) != len(resultado):
        errores.append(
            f"Cantidad de mesas cambió: {len(original)} -> {len(resultado)}"
        )

    campos_originales = {
        "carrera",
        "anio",
        "division",
        "turno",
        "dia",
        "hora",
        "materia",
        "presidente",
        "vocal1",
        "vocal2",
        "conInscriptos",
    }

    for i, (antes, despues) in enumerate(zip(original, resultado)):
        for campo in campos_originales:
            if antes.get(campo) != despues.get(campo):
                errores.append(
                    f"Mesa {i}: cambió el campo '{campo}': "
                    f"{antes.get(campo)!r} -> {despues.get(campo)!r}"
                )

    return errores


# ---------------------------------------------------------------------------
# Reporte
# ---------------------------------------------------------------------------

def escribir_reporte(
    df,
    mesas_originales,
    resultado,
    estados,
    detalles,
    asignadas_ok,
    asignadas_ambiguas,
    errores_integridad,
):
    cantidad_originales = sum(
        1 for mesa in mesas_originales
        if mesa.get("conInscriptos") is True
    )

    cantidad_con_numero = sum(
        1 for mesa in resultado
        if "cantidadInscriptos" in mesa
    )

    lineas = [
        "REPORTE — CANTIDAD DE INSCRIPTOS",
        "=" * 60,
        "",
        f"Excel: {EXCEL_PATH.name}",
        f"Mesas originales: {len(mesas_originales)}",
        f"Mesas conInscriptos=true: {cantidad_originales}",
        f"Mesas con cantidad asignada: {cantidad_con_numero}",
        f"Mesas conInscriptos=true sin número: "
        f"{cantidad_originales - cantidad_con_numero}",
        "",
        "ESTADOS DE LAS CLAVES DEL EXCEL",
        "-" * 60,
    ]

    for clave, valor in estados.most_common():
        lineas.append(f"{clave}: {valor}")

    lineas.extend([
        "",
        f"Asignaciones finales: {asignadas_ok}",
        f"Asignaciones descartadas por ambigüedad múltiple: "
        f"{asignadas_ambiguas}",
        "",
        "VALIDACIÓN DE INTEGRIDAD",
        "-" * 60,
    ])

    if errores_integridad:
        lineas.extend(errores_integridad)
    else:
        lineas.append(
            "OK — ningún campo existente de mesas.json fue modificado."
        )

    lineas.extend([
        "",
        "CASOS NO ASIGNADOS",
        "-" * 60,
    ])

    if detalles:
        lineas.extend(detalles)
    else:
        lineas.append("Ninguno.")

    REPORT_PATH.write_text(
        "\n".join(lineas),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("AGREGAR CANTIDAD DE INSCRIPTOS — MODO SEGURO")
    print("=" * 60)

    df, mesas = cargar_datos()

    print(f"Excel: {EXCEL_PATH.name}")
    print(f"Filas en MESAS A ARMAR: {len(df)}")
    print(f"Mesas en mesas.json: {len(mesas)}")
    print("Procesando...")

    resultado, estados, detalles, asignadas_ok, asignadas_ambiguas = procesar(
        df, mesas
    )

    errores_integridad = validar_integridad(mesas, resultado)

    if errores_integridad:
        print("\nERROR DE INTEGRIDAD.")
        print("NO se escribirá el JSON de salida.")
        for error in errores_integridad:
            print(" -", error)

        escribir_reporte(
            df,
            mesas,
            resultado,
            estados,
            detalles,
            asignadas_ok,
            asignadas_ambiguas,
            errores_integridad,
        )
        raise SystemExit(1)

    with OUTPUT_JSON.open("w", encoding="utf-8") as archivo:
        json.dump(resultado, archivo, ensure_ascii=False, indent=2)

    escribir_reporte(
        df,
        mesas,
        resultado,
        estados,
        detalles,
        asignadas_ok,
        asignadas_ambiguas,
        errores_integridad,
    )

    print("")
    print("RESULTADO")
    print("-" * 60)
    print(f"Mesas totales: {len(resultado)}")
    print(
        "Mesas conInscriptos=true: "
        f"{sum(1 for m in resultado if m.get('conInscriptos') is True)}"
    )
    print(
        "Mesas con cantidad: "
        f"{sum(1 for m in resultado if 'cantidadInscriptos' in m)}"
    )
    print("")
    print("Archivos generados:")
    print(f"  {OUTPUT_JSON}")
    print(f"  {REPORT_PATH}")
    print("")
    print("IMPORTANTE:")
    print("  data/mesas.json NO fue modificado.")
    print("  Los casos dudosos quedaron sin número.")
    print("  Revisar el reporte antes de reemplazar el JSON original.")


if __name__ == "__main__":
    main()
