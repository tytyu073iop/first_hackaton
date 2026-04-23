# filepath: backend/seed_data.py
import json
from pathlib import Path
from math import cos, sin, radians, sqrt
from sqlalchemy.orm import Session
from models import Partner

DEMO_PLAYER = "demo_player_001"


def hex_grid_minsk():
    """Плотная pointy-top гекс-сетка вокруг центра Минска.

    Радиус гекса R задан в градусах широты. Т.к. 1° долготы на широте φ
    короче 1° широты в 1/cos(φ) раз, все долготные смещения делим на cos(φ).
    Для pointy-top соседние центры: dx = R*√3, dy = R*1.5, сдвиг рядов R*√3/2.
    """
    center_lat, center_lng = 53.9045, 27.5615
    R = 0.008
    lat_scale = 1.0 / cos(radians(center_lat))  # расширение долготы

    hexes = []
    idx = 1

    def make_hex(cx_lat, cy_lng, ring):
        nonlocal idx
        vertices = []
        # pointy-top: углы 30°, 90°, 150°, 210°, 270°, 330°
        for k in range(6):
            angle = radians(60 * k + 30)
            vx = cx_lat + R * sin(angle)
            vy = cy_lng + R * cos(angle) * lat_scale
            vertices.append([vx, vy])
        h = {
            "hex_id": f"hex_{idx:03d}",
            "ring": ring,
            "center_lat": cx_lat,
            "center_lng": cy_lng,
            "vertices": vertices,
        }
        idx += 1
        return h

    # axial-координаты, radius колец в гексах
    # radius=6 ≈ 9 км от центра — покрывает территорию внутри МКАД Минска
    grid_radius = 6
    sqrt3 = sqrt(3)
    for q in range(-grid_radius, grid_radius + 1):
        r1 = max(-grid_radius, -q - grid_radius)
        r2 = min(grid_radius, -q + grid_radius)
        for r in range(r1, r2 + 1):
            # pointy-top axial -> offset от центра
            d_lat = R * 1.5 * r
            d_lng = R * sqrt3 * (q + r / 2) * lat_scale
            cx = center_lat + d_lat
            cy = center_lng + d_lng
            ring = max(abs(q), abs(r), abs(-q - r))
            hexes.append(make_hex(cx, cy, ring))

    return hexes


def hex_id_for_point(lat, lng):
    """Возвращает hex_id ячейки сетки, в которую попадает точка (lat, lng).
    Реализовано простым поиском ближайшего центра — достаточно для плотной сетки."""
    grid = hex_grid_minsk()
    lat_scale = 1.0 / cos(radians(53.9045))
    best, best_d = None, float("inf")
    for h in grid:
        dlat = h["center_lat"] - lat
        dlng = (h["center_lng"] - lng) / lat_scale
        d = dlat * dlat + dlng * dlng
        if d < best_d:
            best, best_d = h["hex_id"], d
    return best


PARTNERS_DATA = [
    # Рестораны / кафе (MCC 5812) — центр Минска
    ("Лидо", "restaurant", "5812", 53.9012, 27.5612, 3.5),
    ("Васильки на Немиге", "restaurant", "5812", 53.9048, 27.5478, 4.0),
    ("Раковский Бровар", "restaurant", "5812", 53.9032, 27.5465, 5.0),
    ("Гусь и Клюква", "restaurant", "5812", 53.9105, 27.5651, 3.0),
    ("Тесто", "restaurant", "5812", 53.8978, 27.5689, 4.5),
    ("Хачапури и Вино", "restaurant", "5812", 53.9021, 27.5589, 3.5),
    ("Луна", "restaurant", "5812", 53.9147, 27.5567, 4.0),
    ("Буфет", "restaurant", "5812", 53.8984, 27.5523, 3.0),
    ("Zлата", "restaurant", "5812", 53.9089, 27.5589, 4.5),
    ("Menza", "restaurant", "5812", 53.9112, 27.5612, 3.5),
    ("News Cafe", "restaurant", "5812", 53.9058, 27.5558, 4.0),
    ("Кухмистр", "restaurant", "5812", 53.9062, 27.5498, 5.0),
    ("Васильки на Победителей", "restaurant", "5812", 53.9134, 27.5398, 4.0),
    ("Гранд-кафе", "restaurant", "5812", 53.9022, 27.5548, 4.5),
    ("Grand Cafe", "restaurant", "5812", 53.9002, 27.5682, 4.0),
    ("Pinsk Drinks", "restaurant", "5812", 53.9094, 27.5712, 3.5),
    ("Dolce Vita", "restaurant", "5812", 53.8962, 27.5578, 4.0),
    ("Пицца Лисицца", "restaurant", "5812", 53.9168, 27.5472, 3.5),
    ("Пицца Темпо", "restaurant", "5812", 53.8942, 27.5712, 3.0),
    ("PizzaExpress", "restaurant", "5812", 53.9078, 27.5822, 3.5),
    ("Sushi Karta", "restaurant", "5812", 53.9024, 27.5398, 4.0),
    ("Якитория", "restaurant", "5812", 53.9118, 27.5678, 4.5),
    ("Планета Суши", "restaurant", "5812", 53.8956, 27.5632, 4.0),
    ("McDonald's Независимости", "restaurant", "5812", 53.9032, 27.5672, 2.0),
    ("McDonald's Немига", "restaurant", "5812", 53.9041, 27.5489, 2.0),
    ("Burger King", "restaurant", "5812", 53.9062, 27.5592, 2.5),
    ("KFC", "restaurant", "5812", 53.9049, 27.5636, 2.5),
    ("Starbucks Галерея", "restaurant", "5812", 53.8958, 27.5798, 5.0),
    ("Coffee Like", "restaurant", "5812", 53.9088, 27.5538, 4.0),
    ("Coffee Inn", "restaurant", "5812", 53.9019, 27.5698, 3.5),

    # Продуктовые (MCC 5411)
    ("Евроопт на Немиге", "grocery", "5411", 53.9038, 27.5472, 2.0),
    ("Евроопт на Свердлова", "grocery", "5411", 53.8978, 27.5558, 2.0),
    ("Евроопт Сторожевская", "grocery", "5411", 53.9142, 27.5478, 2.0),
    ("Корона Замок", "grocery", "5411", 53.9108, 27.4842, 2.5),
    ("Корона на Притыцкого", "grocery", "5411", 53.9158, 27.5212, 2.5),
    ("Рублёвский Центр", "grocery", "5411", 53.9098, 27.5698, 2.0),
    ("Виталюр на Ленина", "grocery", "5411", 53.9012, 27.5542, 3.0),
    ("Алми Нямiга", "grocery", "5411", 53.9048, 27.5458, 2.5),
    ("Гиппо", "grocery", "5411", 53.9212, 27.5612, 2.0),
    ("Bigzz", "grocery", "5411", 53.8878, 27.5432, 3.0),
    ("Санта на Романовской", "grocery", "5411", 53.9078, 27.5512, 2.5),
    ("Соседи на Козлова", "grocery", "5411", 53.9178, 27.5898, 3.0),
    ("Соседи на Мясникова", "grocery", "5411", 53.9008, 27.5392, 3.0),
    ("Green Немига", "grocery", "5411", 53.9042, 27.5498, 3.5),
    ("Green Октябрьская", "grocery", "5411", 53.8992, 27.5698, 3.5),
    ("Green на Сторожевской", "grocery", "5411", 53.9152, 27.5418, 3.5),
    ("ProStore", "grocery", "5411", 53.8998, 27.5468, 2.0),

    # Заправки (MCC 5541)
    ("А-100 на Сурганова", "fuel", "5541", 53.9228, 27.5768, 4.0),
    ("А-100 на Немиге", "fuel", "5541", 53.9058, 27.5358, 4.0),
    ("А-100 на Притыцкого", "fuel", "5541", 53.9198, 27.5098, 4.0),
    ("Газпромнефть на Орловской", "fuel", "5541", 53.9312, 27.5498, 5.0),
    ("Газпромнефть Центр", "fuel", "5541", 53.9138, 27.5858, 5.0),
    ("Белоруснефть Победителей", "fuel", "5541", 53.9158, 27.5212, 5.0),
    ("Белоруснефть Маяковского", "fuel", "5541", 53.8862, 27.5498, 5.0),
    ("Лукойл Немига", "fuel", "5541", 53.9088, 27.5298, 4.5),

    # Другое (MCC 5999, 5999)
    ("Wolt", "other", "5999", 53.9042, 27.5612, 7.0),
    ("ZигZаг — электроника", "other", "5999", 53.9028, 27.5682, 4.0),
    ("Электросила", "other", "5999", 53.9098, 27.5512, 3.5),
    ("OZ.by", "other", "5999", 53.9078, 27.5598, 3.0),
    ("21 век", "other", "5999", 53.9018, 27.5478, 4.0),
    ("Папараць-Кветка", "other", "5999", 53.9168, 27.5658, 4.0),
    ("Скарбніца", "other", "5999", 53.9012, 27.5598, 4.5),
    ("Стар Бургер", "other", "5999", 53.9058, 27.5718, 5.0),
    ("Суши Wok", "other", "5999", 53.8998, 27.5558, 5.5),
    ("Дикая Пицца", "other", "5999", 53.9138, 27.5478, 4.5),
    ("LetsBike", "other", "5999", 53.9102, 27.5612, 5.0),
    ("Apteka.by", "other", "5999", 53.9048, 27.5548, 3.5),
    ("Марко обувь", "other", "5999", 53.9028, 27.5632, 4.0),
    ("H&M Галерея", "other", "5999", 53.8958, 27.5798, 4.5),
    ("Zara Dana Mall", "other", "5999", 53.9298, 27.6112, 4.0),
    ("Книгарня Логвiнаў", "other", "5999", 53.9054, 27.5532, 5.0),
]


def _load_osm_partners():
    """Читает backend/partners_osm.json если он есть."""
    p = Path(__file__).resolve().parent / "partners_osm.json"
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, list) or not data:
            return None
        return data
    except Exception:
        return None


MAX_PARTNERS_PER_HEX = 3


def _candidate_partners():
    """Возвращает [(name, category, mcc, lat, lng, cashback), ...] —
    OSM если доступен, иначе встроенный список."""
    osm = _load_osm_partners()
    if osm is not None:
        out = []
        for item in osm:
            name = item.get("name")
            lat = item.get("lat")
            lng = item.get("lng")
            if not name or lat is None or lng is None:
                continue
            out.append((
                name,
                item.get("category", "other"),
                item.get("mcc_code", "5999"),
                float(lat),
                float(lng),
                float(item.get("cashback_percent", 0.0)),
            ))
        return out
    return [(n, c, m, la, ln, cb) for (n, c, m, la, ln, cb) in PARTNERS_DATA]


def _grid_is_stale(session: Session) -> bool:
    """Если хоть у одного партнёра hex_id не совпадает с пересчитанным —
    значит сетка изменилась и партнёров надо пересоздать."""
    sample = session.query(Partner).limit(50).all()
    if not sample:
        return False
    for p in sample:
        if hex_id_for_point(p.lat, p.lng) != p.hex_id:
            return True
    return False


def seed_partners(session: Session):
    """Заполняет таблицу партнёров.

    Правила:
      - источник: partners_osm.json если есть, иначе PARTNERS_DATA;
      - не более MAX_PARTNERS_PER_HEX партнёров на гекс (отбираем с
        наибольшим cashback);
      - в каждом гексе сетки минимум 1 партнёр — если из источника не
        нашлось ни одного попадания, добавляем синтетического в центре.
    Если сетка гексов поменялась относительно того, что в БД, — все
    партнёры пересоздаются."""
    if _grid_is_stale(session):
        session.query(Partner).delete()
        session.commit()

    have_any = session.query(Partner.id).first() is not None
    if have_any:
        return

    grid = hex_grid_minsk()
    grid_ids = {h["hex_id"] for h in grid}

    # 1) распределяем кандидатов по гексам, отбираем top-N по cashback
    by_hex: dict[str, list[tuple]] = {}
    for name, cat, mcc, lat, lng, cb in _candidate_partners():
        hid = hex_id_for_point(lat, lng)
        if hid not in grid_ids:
            continue
        by_hex.setdefault(hid, []).append((name, cat, mcc, lat, lng, cb))

    for hid, lst in by_hex.items():
        lst.sort(key=lambda x: x[5], reverse=True)
        for name, cat, mcc, lat, lng, cb in lst[:MAX_PARTNERS_PER_HEX]:
            session.add(Partner(
                hex_id=hid, name=name, category=cat, mcc_code=mcc,
                lat=lat, lng=lng, cashback_percent=cb,
            ))

    # гарантируем минимум 1 партнёр в каждом гексе сетки
    filled = set(by_hex.keys())
    missing = [h for h in grid if h["hex_id"] not in filled]
    synthetic_pool = [
        ("МТБанк Экспресс", "other", "6011", 3.0),
        ("Партнёрский магазин", "grocery", "5411", 2.0),
        ("Кафе у дома", "restaurant", "5812", 3.5),
        ("Заправка Партнёр", "fuel", "5541", 4.0),
    ]
    for i, h in enumerate(missing):
        name, cat, mcc, cb = synthetic_pool[i % len(synthetic_pool)]
        session.add(Partner(
            hex_id=h["hex_id"],
            name=f"{name} #{i + 1}",
            category=cat,
            mcc_code=mcc,
            lat=h["center_lat"],
            lng=h["center_lng"],
            cashback_percent=cb,
        ))

    session.commit()
