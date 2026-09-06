"""parser_excel.py"""
from __future__ import annotations
import re
from datetime import datetime

def normalizar(t):
    return "" if t is None else " ".join(str(t).replace("\n"," ").split())

def parsear_encabezado(texto):
    texto = normalizar(texto)

    # Normalizaciones de pequeñas diferencias del Excel
    texto = re.sub(r"\bT\s+(Mañana|Tarde|Noche)\b", r"T. \1", texto, flags=re.I)
    texto = re.sub(r"[º°]([A-Z])", r"º \1", texto, flags=re.I)   # 1ºC -> 1º C
    texto = re.sub(r"\s+", " ", texto).strip()

    pats = [

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

        if t == 11:
            return {
                "carrera": "Escenografía",
                "anio": m.group(2),
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
    patron = re.compile(r"EXÁMENES\s+FINALES.*?(\d{4})", re.I)

    for fila in ws.iter_rows(values_only=True):
        for celda in fila:
            texto = normalizar(celda)
            if not texto:
                continue

            m = patron.search(texto)
            if m:
                return int(m.group(1))

    return None

def es_fila_materia(f):
    return len(f)>=3 and normalizar(f[2]) not in ("","Asignatura")

def leer_hoja(ws):
    anio_hoja = obtener_anio_hoja(ws)

    ctx={"carrera":"","anio":"","division":"","turno":""}
    fecha="";hora="";regs=[]
    
    for fila in ws.iter_rows(values_only=True):
        c=list(fila[:6])+[None]*max(0,6-len(fila))
        h = parsear_encabezado(c[0])

        if h:
            ctx = h
            continue

        if normalizar(c[0]):
            print("ENCABEZADO NO RECONOCIDO:", normalizar(c[0]))

        if not es_fila_materia(c):
            continue

        if isinstance(c[0], datetime):
            if anio_hoja is not None:
                fecha_dt = c[0].replace(year=anio_hoja)
            else:
                fecha_dt = c[0]

            fecha = fecha_dt.strftime("%Y-%m-%d")

        elif normalizar(c[0]):
            fecha = normalizar(c[0])

        if normalizar(c[1]):
            hora = normalizar(c[1])

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
            "vocal2": normalizar(c[5])
        })
    return regs
