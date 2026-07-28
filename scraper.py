#!/usr/bin/env python3
"""
Scraper de tabla de mareas de Chipiona (tablademareas.com).

Diseño pensado para que NUNCA se cuele un año equivocado:
- No asume el año/mes por la fecha en la que se ejecuta.
- Lee el año y el mes literalmente escritos en la página ("JUNIO DE 2026").
- Solo guarda si ha reconocido un número razonable de días (>=27).
- Nunca sobrescribe un mes ya guardado con menos días de los que ya tenía.

Se ejecuta una vez al mes (ver .github/workflows/update-mareas.yml) y va
completando data/mareas.json mes a mes, año a año, de forma acumulativa.
"""
import re
import sys
import json
import os
import datetime
import requests

URL = "https://tablademareas.com/es/cadiz/chipiona"
DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "mareas.json")

MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}

MONTH_HEADER_RE = re.compile(
    r"TABLA DE MAREAS CHIPIONA.{0,300}?\b(ENERO|FEBRERO|MARZO|ABRIL|MAYO|JUNIO|"
    r"JULIO|AGOSTO|SEPTIEMBRE|OCTUBRE|NOVIEMBRE|DICIEMBRE)\s+DE\s+(20\d{2})\b",
    re.I | re.S,
)

DAY_RE = re.compile(
    r"(\d{1,2})\s+([LMXJVSD])\s+"
    r"(\d{1,2}:\d{2})\s*h\s+(\d{1,2}:\d{2})\s*h\s+"
    r"((?:\d{1,2}:\d{2}\s*h\s+-?\d,\d\s*m\s*){1,4})"
    r"(\d{1,3})\s+(bajo|medio|alto|muy alto)"
)

TIDE_RE = re.compile(r"(\d{1,2}:\d{2})\s*h\s+(-?\d,\d)\s*m")


def fetch_html():
    r = requests.get(URL, timeout=25, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    return r.text


def strip_tags(html):
    text = re.sub(r"<script.*?</script>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ")
    text = re.sub(r"\s+", " ", text)
    return text


def find_month_year(text):
    m = MONTH_HEADER_RE.search(text)
    if not m:
        return None, None
    mes = MESES[m.group(1).lower()]
    anio = int(m.group(2))
    return anio, mes


def parse_days(text):
    days = []
    seen = set()
    for m in DAY_RE.finditer(text):
        day_num = int(m.group(1))
        if day_num in seen:
            continue
        seen.add(day_num)
        tides = []
        for tm, h in TIDE_RE.findall(m.group(5)):
            hh, mm = tm.split(":")
            minutes = int(hh) * 60 + int(mm)
            height = float(h.replace(",", "."))
            tides.append([minutes, height])
        days.append({
            "day": day_num,
            "sunrise": m.group(3),
            "sunset": m.group(4),
            "tides": tides,
            "coef": int(m.group(6)),
            "activity": m.group(7),
        })
    days.sort(key=lambda d: d["day"])
    return days


def load_existing():
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save(data):
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main():
    html = fetch_html()
    text = strip_tags(html)

    anio, mes = find_month_year(text)
    if not anio or not mes:
        print("No se ha podido reconocer el mes/año en la página. No se guarda nada.")
        return 0  # no es un error fatal, solo no hay nada que actualizar hoy

    days = parse_days(text)
    if len(days) < 27:
        print(f"Solo se reconocieron {len(days)} días para {mes}/{anio}. "
              f"Datos incompletos, no se guarda nada.")
        return 0

    data = load_existing()
    year_key, month_key = str(anio), str(mes)
    data.setdefault(year_key, {})

    existing = data[year_key].get(month_key, {}).get("days", [])
    if len(existing) > len(days):
        print(f"Ya había {len(existing)} días guardados para {mes}/{anio} y ahora "
              f"solo se han leído {len(days)}. Por seguridad, no se sobrescribe.")
        return 0

    data[year_key][month_key] = {
        "days": days,
        "scraped_at": datetime.datetime.utcnow().isoformat() + "Z",
    }
    save(data)
    print(f"Guardado correctamente: {mes}/{anio} con {len(days)} días.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
