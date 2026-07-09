from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

DISPOSITIONS = ("hostile", "unfriendly", "neutral", "friendly", "allied")
DEFAULT_DISPOSITION = "neutral"


class Faction(Base):
    __tablename__ = "faction"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("campaign.id"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    disposition: Mapped[str] = mapped_column(
        String(20), default=DEFAULT_DISPOSITION, server_default=DEFAULT_DISPOSITION, nullable=False
    )
    goals: Mapped[str] = mapped_column(Text, nullable=True)
