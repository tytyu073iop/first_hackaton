"""Добирает партнёров для гексов, которые после fetch_partners_osm.py остались пустыми.

Для каждого пустого гекса делает Overpass-запрос в bbox этого гекса по
shop=supermarket|convenience|mall и amenity=fuel|fast_food|restaurant|cafe|bank|pharmacy.
Берёт первую найденную точку с name и сохраняет в partners_osm.json.

Запуск:  python scripts/fill_empty_hexes.py
"""
import json
import sys
import time
from math import cos, radians
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen, Request

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from seed_data import hex_grid_minsk, hex_id_for_point  # noqa: E402

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
PARTNERS_FILE = Path(__file__).resolve().parent.parent / "partners_osm.json"

# tag -> (category, mcc, cashback)
TAG_MAP = [
    ('shop=supermarket',   ("grocery", "5411", 2.0)),
    ('shop=convenience',   ("grocery", "5411", 2.0)),
    ('shop=mall',          ("other",   "5999", 3.0)),
    ('amenity=fuel',       ("fuel",    "5541", 4.0)),
    ('amenity=restaurant', ("restaurant", "5812", 3.5)),
    ('amenity=fast_food',  ("restaurant", "5812", 2.5)),
    ('amenity=cafe',       ("restaurant", "5812", 4.0)),
    ('amenity=pharmacy',   ("other",   "5912", 3.0)),
    ('amenity=bank',       ("other",   "6011", 0.0)),
    ('shop=clothes',       ("other",   "5651", 4.0)),
    ('shop=bakery',        ("restaurant", "5812", 3.0)),
]


def hex_bbox(center_lat, center_lng, R_deg):
    """Грубый bbox гекса: квадрат стороной 2R вокруг центра."""
    lat_scale = 1.0 / cos(radians(center_lat))
    return (
        center_lat - R_deg,
        center_lng - R_deg * lat_scale,
        center_lat + R_deg,
        center_lng + R_deg * lat_scale,
    )


def query_for_hex(s, w, n, e):
    parts = []
    for tag, _ in TAG_MAP:
        k, v = tag.split("=")
        parts.append(f'  node["{k}"="{v}"]["name"]({s},{w},{n},{e});')
        parts.append(f'  way["{k}"="{v}"]["name"]({s},{w},{n},{e});')
    body = "[out:json][timeout:25];\n(\n" + "\n".join(parts) + "\n);\nout center tags;"
    return body


def fetch(query: str):
    body = urlencode({"data": query}).encode("utf-8")
    req = Request(
        OVERPASS_URL,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "User-Agent": "fog-of-war-mtbank/1.0 (hackathon, fill-empty)",
        },
    )
    with urlopen(req, timeout=60) as r:
        return json.load(r)


def classify(tags):
    for tag, meta in TAG_MAP:
        k, v = tag.split("=")
        if tags.get(k) == v:
            return meta
    return ("other", "5999", 3.0)


def main():
    grid = hex_grid_minsk()
    all_ids = {h["hex_id"] for h in grid}
    by_id = {h["hex_id"]: h for h in grid}

    data = json.loads(PARTNERS_FILE.read_text(encoding="utf-8"))
    covered = set()
    for p in data:
        hid = hex_id_for_point(p["lat"], p["lng"])
        if hid in all_ids:
            covered.add(hid)

    empty = sorted(all_ids - covered)
    print(f"empty hexes: {len(empty)}")

    R = 0.008  # должен совпадать с seed_data.hex_grid_minsk
    added = 0
    for hid in empty:
        h = by_id[hid]
        s, w, n, e = hex_bbox(h["center_lat"], h["center_lng"], R)
        q = query_for_hex(s, w, n, e)
        try:
            res = fetch(q)
        except Exception as ex:
            print(f"{hid}: error {ex}")
            time.sleep(5)
            continue

        chosen = None
        for el in res.get("elements", []):
            tags = el.get("tags", {}) or {}
            name = tags.get("name")
            if not name:
                continue
            if el["type"] == "node":
                lat, lon = el.get("lat"), el.get("lon")
            else:
                c = el.get("center") or {}
                lat, lon = c.get("lat"), c.get("lon")
            if lat is None or lon is None:
                continue
            # должен попасть в этот же hex
            if hex_id_for_point(lat, lon) != hid:
                continue
            cat, mcc, cb = classify(tags)
            chosen = {
                "name": name,
                "brand": tags.get("brand", ""),
                "category": cat,
                "mcc_code": mcc,
                "cashback_percent": cb,
                "lat": lat,
                "lng": lon,
            }
            break

        if chosen:
            data.append(chosen)
            added += 1
            print(f"{hid}: + {chosen['name']} ({chosen['category']})")
        else:
            print(f"{hid}: ничего не найдено")
        time.sleep(1.2)

    PARTNERS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"добавлено {added} партнёров, итого {len(data)}")


if __name__ == "__main__":
    main()
