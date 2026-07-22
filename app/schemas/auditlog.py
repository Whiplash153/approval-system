from pydantic import BaseModel, Field
from datetime import datetime

class AuditLogCreateSchema(BaseModel):

    proposal_id: int
    user_id: int
    action: str = Field(min_length=2, max_length=50)

class AuditLogResponseSchema(BaseModel):

    id: int
    proposal_id: int
    user_id: int
    action: str
    created_at: datetime