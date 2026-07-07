from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.models import AppSetting


def get_setting(db: Session, key: str, default: str | None = None) -> str | None:
    row = db.get(AppSetting, key)
    return row.value if row is not None else default


def set_setting(db: Session, key: str, value: str) -> None:
    row = db.get(AppSetting, key)
    if row is None:
        db.add(AppSetting(key=key, value=value))
    else:
        row.value = value
    db.commit()
