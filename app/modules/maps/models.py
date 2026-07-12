from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

DIAGONAL_RULES = ("chebyshev", "five_ten_five", "euclidean", "manhattan")


class Map(Base):
    __tablename__ = "map"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("campaign.id"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    image_path: Mapped[str | None] = mapped_column(String(500))
    image_w: Mapped[int | None] = mapped_column(Integer)
    image_h: Mapped[int | None] = mapped_column(Integer)
    grid_size_px: Mapped[int] = mapped_column(
        Integer, nullable=False, default=70, server_default="70"
    )
    grid_offset_x: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    grid_offset_y: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    grid_visible: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="1"
    )
    feet_per_square: Mapped[int] = mapped_column(
        Integer, nullable=False, default=5, server_default="5"
    )
    diagonal_rule: Mapped[str] = mapped_column(
        String(20), nullable=False, default="chebyshev", server_default="chebyshev"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0"
    )
