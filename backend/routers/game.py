# filepath: backend/routers/game.py
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from models import SessionLocal, Partner, PlayerProgress, Achievement, Reward
from seed_data import hex_grid_minsk
from achievement_engine import AchievementEngine

router = APIRouter(prefix="/api")

HEX_TTL = timedelta(minutes=1)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class TransactionIn(BaseModel):
    player_id: str
    merchant_name: str
    mcc_code: str
    amount: float
    currency: str = "BYN"
    timestamp: str | None = None
    partner_id: int | None = None


@router.get("/hexes/{player_id}")
def get_hexes(player_id: str, db: Session = Depends(get_db)):
    grid = hex_grid_minsk()
    cutoff = datetime.utcnow() - HEX_TTL
    unlocked_ids = {
        pp.hex_id for pp in
        db.query(PlayerProgress)
        .filter(PlayerProgress.player_id == player_id)
        .filter(PlayerProgress.unlocked_at >= cutoff)
        .all()
    }
    partners_by_hex = {}
    for p in db.query(Partner).all():
        partners_by_hex.setdefault(p.hex_id, []).append(p)

    hexes_out = []
    for h in grid:
        hid = h["hex_id"]
        is_unlocked = hid in unlocked_ids
        partner_data = None
        if is_unlocked and partners_by_hex.get(hid):
            p = partners_by_hex[hid][0]
            partner_data = {
                "name": p.name,
                "category": p.category,
                "cashback_percent": p.cashback_percent,
            }

        hexes_out.append({
            "hex_id": hid,
            "ring": h["ring"],
            "center": {"lat": h["center_lat"], "lng": h["center_lng"]},
            "vertices": h["vertices"],
            "is_unlocked": is_unlocked,
            "partner": partner_data,
            "active_quest": None,
        })

    ach_count = db.query(Achievement).filter_by(player_id=player_id).count()

    return {
        "hexes": hexes_out,
        "stats": {
            "total": len(grid),
            "unlocked": len(unlocked_ids),
            "achievements_count": ach_count,
        },
    }


@router.post("/transaction")
def post_transaction(tx: TransactionIn, db: Session = Depends(get_db)):
    player_id = tx.player_id
    if not player_id:
        return {"hex_unlocked": None, "reward": None, "new_achievements": [], "message": "Нет player_id"}

    partner = None
    if tx.partner_id is not None:
        partner = db.query(Partner).filter_by(id=tx.partner_id).first()
    if partner is None:
        partner = db.query(Partner).filter_by(name=tx.merchant_name).first()
    if not partner:
        return {
            "hex_unlocked": None,
            "reward": None,
            "new_achievements": [],
            "message": f"Партнёр '{tx.merchant_name}' не найден",
        }

    target_hex = partner.hex_id
    cutoff = datetime.utcnow() - HEX_TTL
    active = (
        db.query(PlayerProgress)
        .filter(PlayerProgress.player_id == player_id)
        .filter(PlayerProgress.hex_id == target_hex)
        .filter(PlayerProgress.unlocked_at >= cutoff)
        .first()
    )

    hex_unlocked = None
    new_achievements = []

    if not active:
        now = datetime.utcnow()
        stale = db.query(PlayerProgress).filter_by(
            player_id=player_id, hex_id=target_hex
        ).first()
        is_rescue = False
        if stale:
            stale.unlocked_at = now
            stale.quest_type = "rescue"
            is_rescue = True
        else:
            db.add(PlayerProgress(
                player_id=player_id,
                hex_id=target_hex,
                unlocked_at=now,
                quest_type="purchase",
            ))
        db.commit()
        hex_unlocked = target_hex

        ts = datetime.utcnow()
        if tx.timestamp:
            try:
                ts = datetime.fromisoformat(tx.timestamp.replace("Z", "+00:00"))
            except Exception:
                ts = datetime.utcnow()

        event = {
            "type": "hex_unlocked",
            "hex_id": target_hex,
            "timestamp": ts,
            "mcc": tx.mcc_code,
            "is_rescue": is_rescue,
        }
        new_achievements = AchievementEngine.check_and_award(db, player_id, event)

    reward = {
        "type": "cashback",
        "value": partner.cashback_percent,
        "label": f"{partner.cashback_percent}% кэшбэк в {partner.name}",
    }

    return {
        "hex_unlocked": hex_unlocked,
        "reward": reward,
        "new_achievements": new_achievements,
        "partner": {
            "name": partner.name,
            "category": partner.category,
            "hex_id": partner.hex_id,
        },
    }


def _point_in_polygon(lat: float, lng: float, vertices) -> bool:
    """Ray casting для точки в многоугольнике. vertices = [[lat, lng], ...]."""
    inside = False
    n = len(vertices)
    j = n - 1
    for i in range(n):
        yi, xi = vertices[i][0], vertices[i][1]
        yj, xj = vertices[j][0], vertices[j][1]
        intersects = ((yi > lat) != (yj > lat)) and (
            lng < (xj - xi) * (lat - yi) / ((yj - yi) or 1e-12) + xi
        )
        if intersects:
            inside = not inside
        j = i
    return inside


@router.get("/partners")
def get_partners(db: Session = Depends(get_db)):
    partners = db.query(Partner).order_by(Partner.name).all()
    grid_by_id = {h["hex_id"]: h for h in hex_grid_minsk()}

    out = []
    for p in partners:
        h = grid_by_id.get(p.hex_id)
        if not h:
            continue
        if not _point_in_polygon(p.lat, p.lng, h["vertices"]):
            continue
        out.append({
            "id": p.id,
            "name": p.name,
            "category": p.category,
            "mcc_code": p.mcc_code,
            "lat": p.lat,
            "lng": p.lng,
            "cashback_percent": p.cashback_percent,
            "hex_id": p.hex_id,
        })
    return {"partners": out}


@router.get("/player/{player_id}/profile")
def get_profile(player_id: str, db: Session = Depends(get_db)):
    cutoff = datetime.utcnow() - HEX_TTL
    progress = (
        db.query(PlayerProgress)
        .filter(PlayerProgress.player_id == player_id)
        .filter(PlayerProgress.unlocked_at >= cutoff)
        .all()
    )
    unlocked_ids = [p.hex_id for p in progress]

    achs = db.query(Achievement).filter_by(player_id=player_id).all()
    ach_list = [
        {
            "code": a.code,
            "name": a.name,
            "description": a.description,
            "unlocked_at": a.unlocked_at.isoformat(),
        }
        for a in achs
    ]

    total = len(hex_grid_minsk())

    return {
        "player_id": player_id,
        "unlocked_hexes": unlocked_ids,
        "unlocked_count": len(unlocked_ids),
        "total_hexes": total,
        "achievements": ach_list,
        "active_quest": None,
    }


@router.get("/rewards/{player_id}")
def list_rewards(player_id: str, db: Session = Depends(get_db)):
    """Возвращает активные (не использованные и не просроченные) промокоды игрока."""
    now = datetime.utcnow()
    rows = (
        db.query(Reward)
        .filter(Reward.player_id == player_id)
        .order_by(Reward.created_at.desc())
        .all()
    )
    active, used, expired = [], [], []
    for r in rows:
        item = {
            "id": r.id,
            "code": r.code,
            "title": r.title,
            "description": r.description,
            "reward_type": r.reward_type,
            "value": r.value,
            "scope": r.scope,
            "source_code": r.source_code,
            "created_at": r.created_at.isoformat(),
            "expires_at": r.expires_at.isoformat(),
            "used_at": r.used_at.isoformat() if r.used_at else None,
        }
        if r.used_at is not None:
            used.append(item)
        elif r.expires_at < now:
            expired.append(item)
        else:
            active.append(item)
    return {"active": active, "used": used, "expired": expired}


@router.post("/rewards/{reward_id}/use")
def use_reward(reward_id: int, db: Session = Depends(get_db)):
    r = db.query(Reward).filter_by(id=reward_id).first()
    if not r:
        return {"ok": False, "error": "not_found"}
    if r.used_at is not None:
        return {"ok": False, "error": "already_used"}
    if r.expires_at < datetime.utcnow():
        return {"ok": False, "error": "expired"}
    r.used_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "used_at": r.used_at.isoformat()}
