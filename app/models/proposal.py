from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, DateTime, Enum
from datetime import datetime

from app.db.base import Base
from app.models.enums import ProposalStatus

class Proposal(Base):
    __tablename__ = "proposals"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[ProposalStatus] = mapped_column(Enum(ProposalStatus), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.utcnow())
    deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    author: Mapped["User"] = relationship(back_populates="created_proposals")
    votes: Mapped[list["Vote"]] = relationship(back_populates="proposal")
    participants: Mapped[list["Participant"]] = relationship(back_populates="proposal")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="proposal")
