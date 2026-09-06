"""parser_excel.py"""
from __future__ import annotations
import re
from datetime import datetime

COLORES_BLANCO = {"FFFFFF","FFFFFFFF","00FFFFFF"}

def obtener_color_rgb(celda):
    fill=getattr(celda,"fill",None)
    if fill is None or fill.fill_type in (None,""):
        return None
    fg=getattr(fill,"fgColor",None)
    if fg is None:
        return None
    color=fg.rgb or fg.value or fg.indexed
    return None if color is None else str(color).upper()

def estado_inscriptos(celda):
    color = obtener_color_rgb(celda)

    # Sin relleno
    if color is None:
        return False

    # Blanco
    if color in COLORES_BLANCO:
        return False

    # Cualquier otro relleno indica inscriptos
    return True


def normalizar(t):
    return "" if t is None else " ".join(str(t).replace("\n"," ").split())

def parsear_encabezado(texto):
    texto = normalizar(texto)

    # Normalizaciones de pequeñas diferencias del Excel
    texto = re.sub(r"\bT\s+(Mañana|Tarde|Noche)\b", r"T. \1", texto, flags=re.I)
    texto = re.sub(r"[º°]([A-Z])", r"º \1", texto, flags=re.I)   # 1ºC -> 1º C
    texto = re.sub(r"\s+", " ", texto).strip()

    pats = [

        # Tecnicatura en Fotografía 3º T. Mañana
        # Tecnicatura en Medios Audiovisuales 2º T. Tarde
        # Tecnicatura en Diseño Gráfico 4º T. Noche
        # Tecnicatura en Realización 1º T. Mañana
        (r"^(.*?)\s+(\d+)[º°]?\s+T\.?\s*(Mañana|Tarde|Noche)$", 13),
        
        # PROFESORADO EN ARTES VISUALES 1º D - T. Noche
        (r"^PROFESORADO EN ARTES VISUALES\s+(\d+)[º°]?\s+([A-Z])\s*-\s*T\.?\s*(Mañana|Tarde|Noche)$", 6),

        # 2º A - Profesorado - Turno Mañana
        # 4º A - Profesorado - Turno Mañana EDI - Profesorado
        (r"^(\d+)[º°]?\s+([A-Z])\s*-\s*Profesorado\s*-\s*Turno\s+(Mañana|Tarde|Noche)(?:\s+.*)?$", 9),

        # Artes y Medios Audiovisuales - 1º año
        (r"^(.*?)\s*-\s*(\d+)[º°]?\s*año$", 8),

        # Escenografía 2º T. Tarde
        (r"^(Escenograf(?:ia|ía))\s+(\d+)[º°]?\s+T\.?\s*(Mañana|Tarde|Noche)$", 11),

        # Tecnicatura en Ilustración 1º C T. Noche
        (r"^(.*?)\s+(\d+)[º°]?\s+([A-Z])\s+T\.?\s*(Mañana|Tarde|Noche)$", 2),

        # 3 B Ilustracion - Turno Tarde
        (r"^(\d+)[º°]?\s+([A-Z])\s+(Ilustracion|Ilustración)\s*-\s*Turno\s+(Mañana|Tarde|Noche)$", 10),

        # 1º C - TECNICATURA EN DISEÑO GRÁFICO - T. Noche
        # 4º C - DISEÑO GRÁFICO - T. Noche
        (r"^(\d+)[º°]?\s+([A-Z])\s*-\s*(.*?)\s*-\s*T\.?\s*(Mañana|Tarde|Noche)$", 12),

        # 1º A - TECNICATURA EN ...
        (r"^(\d+)[º°]?\s+([A-Z])\s*-\s*(.*?)\s*-\s*Turno\s+(Mañana|Tarde|Noche)$", 1),

        # ... 3º Año A T. Mañana
        (r"^(.*?)\s+(\d+)[º°]?\s+Año\s+([A-Z])\s+T\.\s*(Mañana|Tarde|Noche)$", 3),

        # ... 3º Año T. Mañana
        (r"^(.*?)\s+(\d+)[º°]?\s+Año\s+T\.\s*(Mañana|Tarde|Noche)$", 4),

        # FoBa
        (r"^(.*?)\s*-\s*Formacion Basica\s+Turno\s+(Mañana|Tarde|Noche)$", 5),
    ]

    for p, t in pats:
        m = re.match(p, texto, re.I)
        if not m:
            continue

        print("MATCH:", t, "->", texto)

        if t == 6:
            return {
                "carrera": "Profesorado En Artes Visuales",
                "anio": m.group(1),
                "division": m.group(2).upper(),
                "turno": m.group(3).title()
            }

        if t == 9:
            return {
                "carrera": "Profesorado En Artes Visuales",
                "anio": m.group(1),
                "division": m.group(2).upper(),
                "turno": m.group(3).title()
            }

        if t == 8:
            return {
                "carrera": m.group(1).title(),
                "anio": m.group(2),
                "division": "",
                "turno": ""
            }

        if t == 10:
            return {
                "carrera": "Ilustración",
                "anio": m.group(1),
                "division": m.group(2).upper(),
                "turno": m.group(4).title()
            }

        if t == 13:
            c = re.sub(r"^Tecnicatura en\s+", "", m.group(1), flags=re.I)

            return {
                "carrera": c.title(),
                "anio": m.group(2),
                "division": "",
                "turno": m.group(3).title()
            }

        if t == 11:

            anio = m.group(2)

            if anio == "0":
                return {
                    "carrera": "FoBa Escenografía",
                    "anio": "FoBa",
                    "division": "",
                    "turno": m.group(3).title()
                }

            return {
                "carrera": "Escenografía",
                "anio": anio,
                "division": "",
                "turno": m.group(3).title()
            }

        if t == 12:
            c = re.sub(r"^TECNICATURA EN\s+", "", m.group(3), flags=re.I)
            return {
                "carrera": c.title(),
                "anio": m.group(1),
                "division": m.group(2).upper(),
                "turno": m.group(4).title()
            }

        if t == 1:
            c = re.sub(r"^TECNICATURA EN\s+", "", m.group(3), flags=re.I)
            return {
                "carrera": c.title(),
                "anio": m.group(1),
                "division": m.group(2).upper(),
                "turno": m.group(4).title()
            }

        if t == 2:
            c = re.sub(r"^Tecnicatura en\s+", "", m.group(1), flags=re.I)
            return {
                "carrera": c.title(),
                "anio": m.group(2),
                "division": m.group(3).upper(),
                "turno": m.group(4).title()
            }

        if t == 3:
            return {
                "carrera": m.group(1).title(),
                "anio": m.group(2),
                "division": m.group(3).upper(),
                "turno": m.group(4).title()
            }

        if t == 4:
            return {
                "carrera": m.group(1).title(),
                "anio": m.group(2),
                "division": "",
                "turno": m.group(3).title()
            }

        if t == 5:
            return {
                "carrera": m.group(1).title(),
                "anio": "FoBa",
                "division": "",
                "turno": m.group(2).title()
            }

    return None

def obtener_anio_hoja(ws):
    """
    Obtiene el año de la planilla buscando un año de cuatro cifras
    en cualquier celda de la hoja.
    """

    patron = re.compile(r"\b(20\d{2})\b")

    # 1) Busca en todas las celdas con texto
    for fila in ws.iter_rows():
        for celda in fila:
            valor = celda.value

            if valor is None:
                continue

            # Si ya es una fecha de Excel
            if isinstance(valor, datetime):
                return valor.year

            texto = str(valor)

            m = patron.search(texto)
            if m:
                return int(m.group(1))

    # 2) Si no encontró nada, usa el año actual por defecto
    return datetime.now().year

def es_fila_materia(f):
    return len(f)>=3 and normalizar(f[2]) not in ("","Asignatura")

def leer_hoja(ws):
    anio_hoja = obtener_anio_hoja(ws)

    ctx = {
        "carrera": "",
        "anio": "",
        "division": "",
        "turno": ""
    }

    fecha = ""
    hora = ""
    regs = []

    for fila in ws.iter_rows():

        celdas = list(fila[:6]) + [None] * max(0, 6 - len(fila))
        c = [x.value if x is not None else None for x in celdas]

        # -------------------------------------------------
        # Cambio de encabezado
        # -------------------------------------------------

        encabezado = parsear_encabezado(c[0])

        if encabezado:
            ctx = encabezado
            continue

        # -------------------------------------------------
        # Cambio de fecha
        # -------------------------------------------------

        if c[0] is not None:

            if isinstance(c[0], datetime):

                if anio_hoja is not None:
                    fecha = c[0].replace(year=anio_hoja).strftime("%Y-%m-%d")
                else:
                    fecha = c[0].strftime("%Y-%m-%d")

            else:

                texto = normalizar(c[0])

                if texto:

                    # Normalizaciones para los distintos formatos del Excel
                    t = texto.lower()
                    t = t.replace("miércoles", "miercoles")
                    t = re.sub(r"\s+", " ", t)
                    t = re.sub(r"\s*/\s*", "/", t)

                    # Busca una fecha en cualquier parte del texto
                    m = re.search(r"(\d{1,2})/(\d{1,2})(?:/(\d{4}))?", t)

                    if m:

                        dia = int(m.group(1))
                        mes = int(m.group(2))

                        if m.group(3):
                            anio = int(m.group(3))
                        else:
                            anio = anio_hoja

                        if anio:
                            fecha = f"{anio:04d}-{mes:02d}-{dia:02d}"
                        else:
                            fecha = texto

                    elif t not in ("dia", "día", "dia:", "día:"):
                        print("ENCABEZADO NO RECONOCIDO:", texto)

        # -------------------------------------------------
        # Hora
        # -------------------------------------------------

        if normalizar(c[1]):
            hora = normalizar(c[1])

        # -------------------------------------------------
        # Materia
        # -------------------------------------------------

        if not es_fila_materia(c):
            continue

        regs.append({
            "carrera": ctx["carrera"],
            "anio": ctx["anio"],
            "division": ctx["division"],
            "turno": ctx["turno"],
            "dia": fecha,
            "hora": hora,
            "materia": normalizar(c[2]),
            "presidente": normalizar(c[3]),
            "vocal1": normalizar(c[4]),
            "vocal2": normalizar(c[5]),
            "conInscriptos": estado_inscriptos(celdas[2])
        })

    con = sum(1 for r in regs if r["conInscriptos"])

    print(f"Mesas generadas: {len(regs)}")
    print(f"Con inscriptos: {con}")
    print(f"Sin inscriptos: {len(regs)-con}")

    return regs