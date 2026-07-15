from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.core.registry import Metric, Registry

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def render_cards(registry: Registry, db: Session | None, campaign_id: int) -> list[dict]:
    """Render every registered dashboard card, isolating failures.

    A module's card is rendered by the module itself; core only collects the
    fragment. A card that raises yields a placeholder rather than taking the
    whole home page down with it.
    """
    rendered: list[dict] = []
    for card in registry.dashboard_cards():
        try:
            html = card.render(db, campaign_id)
            failed = False
        except Exception:
            logger.exception("dashboard card %s failed to render", card.key)
            if db is not None:
                db.rollback()
            html = ""
            failed = True
        rendered.append(
            {
                "key": card.key,
                "title": card.title,
                "span": card.span,
                "html": html,
                "failed": failed,
            }
        )
    return rendered


def collect_metrics(registry: Registry, db: Session | None, campaign_id: int) -> list[Metric]:
    metrics: list[Metric] = []
    for provider in registry.metric_providers:
        try:
            metrics.extend(provider(db, campaign_id))
        except Exception:
            logger.exception("dashboard metric provider failed")
            if db is not None:
                db.rollback()
    return sorted(metrics, key=lambda m: m.order)
