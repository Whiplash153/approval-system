from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, UniqueConstraint, String
from app.db.base import Base

class Participant(Base):
    __tablename__ = "participants"
    __table_args__ = (UniqueConstraint("user_id", "proposal_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    proposal_id: Mapped[int] = mapped_column(ForeignKey("proposals.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    role: Mapped[str] = mapped_column(String, nullable=False, default="voter")

    proposal: Mapped["Proposal"] = relationship(back_populates="participants")
    user: Mapped["User"] = relationship(back_populates="participations")

