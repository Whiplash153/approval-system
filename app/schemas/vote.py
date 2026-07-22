from pydantic import BaseModel
from typing import Literal
from app.models.enums import ProposalStatus

class VoteCreateSchema(BaseModel):

    value: Literal["approve", "reject"]
    user_id: int
    proposal_id: int

class VoteResponseSchema(BaseModel):

    id: int
    value: Literal["approve", "reject"]
    user_id: int
    proposal_id: int
    status: ProposalStatus