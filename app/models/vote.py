from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, UniqueConstraint
from app.db.base import Base

class Vote(Base):
    __tablename__ = "votes"
    __table_args__ = (UniqueConstraint("user_id", "proposal_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    value: Mapped[str] = mapped_column(String, nullable=False)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    proposal_id: Mapped[int] = mapped_column(ForeignKey("proposals.id"))

    proposal: Mapped["Proposal"] = relationship(back_populates="votes")
    user: Mapped["User"] = relationship(back_populates="votes")
