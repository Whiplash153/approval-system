from app.db.session import engine
from app.db.base import Base

import app.models.user
import app.models.proposal
import app.models.vote

Base.metadata.create_all(bind=engine)