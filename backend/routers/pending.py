# filepath: backend/routers/pending.py
import os
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from models import SessionLocal, Partner, PendingTransaction, PlayerProgress, User, Achievement
from achievement_engine import AchievementEngine

router = APIRouter(prefix="/api")

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "demo-admin-token")

HEX_TTL = timedelta(minutes=0.5)


def _active_unlock(db: Session, player_id: str, hex_id: str) -> PlayerProgress | None:
    cutoff = datetime.utcnow() - HEX_TTL
    return (
        db.query(PlayerProgress)
        .filter(PlayerProgress.player_id == player_id)
        .filter(PlayerProgress.hex_id == hex_id)
        .filter(PlayerProgress.unlocked_at >= cutoff)
        .first()
    )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class PendingIn(BaseModel):
    player_id: str
    merchant_name: str
    amount: float = 0.0
    mcc_code: str = ""
    partner_id: int | None = None


@router.post("/pending")
def create_pending(body: PendingIn, db: Session = Depends(get_db)):
    """Создать отложенную транзакцию. Гекс не открывается до consume.

    Если передан partner_id — берём конкретную точку (важно когда у партнёра
    с одним именем несколько локаций). Иначе fallback по имени."""
    partner = None
    if body.partner_id is not None:
        partner = db.query(Partner).filter_by(id=body.partner_id).first()
    if partner is None:
        partner = db.query(Partner).filter_by(name=body.merchant_name).first()
    if not partner:
        raise HTTPException(status_code=404, detail=f"Партнёр '{body.merchant_name}' не найден")

    if _active_unlock(db, body.player_id, partner.hex_id):
        return {"created": False, "reason": "already_unlocked"}

    existing = db.query(PendingTransaction).filter_by(
        player_id=body.player_id,
        partner_id=partner.id,
        consumed_at=None,
    ).first()
    if existing:
        return {"created": False, "reason": "already_pending", "pending_id": existing.id}

    pt = PendingTransaction(
        player_id=body.player_id,
        partner_id=partner.id,
        partner_name=partner.name,
        amount=body.amount,
        mcc_code=body.mcc_code or partner.mcc_code,
    )
    db.add(pt)
    db.commit()
    db.refresh(pt)
    return {"created": True, "pending_id": pt.id}


@router.get("/pending/{player_id}")
def list_pending(player_id: str, db: Session = Depends(get_db)):
    items = db.query(PendingTransaction).filter_by(
        player_id=player_id, consumed_at=None
    ).order_by(PendingTransaction.created_at.desc()).all()

    pids = {i.partner_id for i in items if i.partner_id is not None}
    names = {i.partner_name for i in items if i.partner_id is None}
    by_id = {p.id: p for p in db.query(Partner).filter(Partner.id.in_(pids)).all()} if pids else {}
    by_name = {p.name: p for p in db.query(Partner).filter(Partner.name.in_(names)).all()} if names else {}

    out = []
    for i in items:
        p = by_id.get(i.partner_id) if i.partner_id is not None else by_name.get(i.partner_name)
        if not p:
            continue
        out.append({
            "pending_id": i.id,
            "partner_id": p.id,
            "partner_name": p.name,
            "category": p.category,
            "cashback_percent": p.cashback_percent,
            "lat": p.lat,
            "lng": p.lng,
            "hex_id": p.hex_id,
            "amount": i.amount,
            "created_at": i.created_at.isoformat(),
        })
    return {"pending": out}


@router.post("/pending/{pending_id}/consume")
def consume_pending(pending_id: int, db: Session = Depends(get_db)):
    pt = db.query(PendingTransaction).filter_by(id=pending_id).first()
    if not pt:
        raise HTTPException(status_code=404, detail="Не найдено")
    if pt.consumed_at is not None:
        raise HTTPException(status_code=400, detail="Уже использовано")

    partner = None
    if pt.partner_id is not None:
        partner = db.query(Partner).filter_by(id=pt.partner_id).first()
    if partner is None:
        partner = db.query(Partner).filter_by(name=pt.partner_name).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Партнёр удалён")

    target_hex = partner.hex_id
    hex_unlocked = None
    new_achievements = []
    now = datetime.utcnow()

    active = _active_unlock(db, pt.player_id, target_hex)
    is_rescue = False
    if not active:
        stale = db.query(PlayerProgress).filter_by(
            player_id=pt.player_id, hex_id=target_hex
        ).first()
        if stale:
            # Если запись была — это re-unlock протухшего гекса (rescue)
            stale.unlocked_at = now
            stale.quest_type = "rescue"
            is_rescue = True
        else:
            db.add(PlayerProgress(
                player_id=pt.player_id,
                hex_id=target_hex,
                unlocked_at=now,
                quest_type="pending_purchase",
            ))
        hex_unlocked = target_hex

    pt.consumed_at = now
    db.flush()

    # 1) ивент про открытие (если открыли)
    if hex_unlocked:
        event = {
            "type": "hex_unlocked",
            "hex_id": target_hex,
            "timestamp": now,
            "mcc": pt.mcc_code,
            "is_rescue": is_rescue,
        }
        new_achievements += AchievementEngine.check_and_award(db, pt.player_id, event)

    # 2) ивент про сумму транзакции (всегда — для big_tx / thrifty)
    tx_event = {
        "type": "transaction_consumed",
        "amount": pt.amount,
        "mcc": pt.mcc_code,
        "timestamp": now,
    }
    new_achievements += AchievementEngine.check_and_award(db, pt.player_id, tx_event)
    db.commit()

    return {
        "hex_unlocked": hex_unlocked,
        "reward": {
            "type": "cashback",
            "value": partner.cashback_percent,
            "label": f"{partner.cashback_percent}% кэшбэк в {partner.name}",
        },
        "new_achievements": new_achievements,
        "partner": {
            "name": partner.name,
            "category": partner.category,
            "hex_id": partner.hex_id,
        },
    }


# ---------- ADMIN (вариант C) ----------

class AdminPushIn(BaseModel):
    player_id: str
    merchant_name: str
    amount: float = 0.0
    partner_id: int | None = None


def _check_admin(token: str | None):
    if not token or token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Неверный админ-токен")


@router.get("/admin/users")
def admin_users(x_admin_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    _check_admin(x_admin_token)
    users = db.query(User).order_by(User.created_at.desc()).all()
    return {
        "users": [
            {
                "player_id": u.id,
                "name": u.name,
                "recovery_code": u.recovery_code,
                "created_at": u.created_at.isoformat(),
            }
            for u in users
        ]
    }


@router.post("/admin/push")
def admin_push(
    body: AdminPushIn,
    x_admin_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    """Админ от имени банка создаёт pending-транзакцию произвольному игроку."""
    _check_admin(x_admin_token)
    user = db.query(User).filter_by(id=body.player_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Игрок не найден")

    partner = None
    if body.partner_id is not None:
        partner = db.query(Partner).filter_by(id=body.partner_id).first()
    if partner is None:
        partner = db.query(Partner).filter_by(name=body.merchant_name).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Партнёр не найден")

    if _active_unlock(db, body.player_id, partner.hex_id):
        return {"created": False, "reason": "already_unlocked"}

    existing = db.query(PendingTransaction).filter_by(
        player_id=body.player_id,
        partner_id=partner.id,
        consumed_at=None,
    ).first()
    if existing:
        return {"created": False, "reason": "already_pending", "pending_id": existing.id}

    pt = PendingTransaction(
        player_id=body.player_id,
        partner_id=partner.id,
        partner_name=partner.name,
        amount=body.amount,
        mcc_code=partner.mcc_code,
    )
    db.add(pt)
    db.commit()
    db.refresh(pt)
    return {"created": True, "pending_id": pt.id}
