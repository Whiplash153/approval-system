from sqlalchemy.orm import Session
from app.models.audit import AuditLog

class AuditLogRepo:
    def __init__(self, session: Session):
        self.session = session

    def create(self, audit_log: AuditLog):
        self.session.add(audit_log)