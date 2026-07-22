from pydantic import BaseModel, Field
from app.models.enums import ProposalStatus
from datetime import datetime
from app.schemas.vote import VoteResponseSchema

class ProposalCreateSchema(BaseModel):

    title: str = Field(min_length=2, max_length=50)
    description: str = Field(min_length=2, max_length=500)
    author_id: int
    participant_ids: list[int]
    deadline: datetime | None = None

class ProposalResponseSchema(BaseModel):

    id: int
    title: str = Field(min_length=2, max_length=50)
    description: str = Field(min_length=2, max_length=500)
    author_id: int
    status: ProposalStatus
    created_at: datetime
    deadline: datetime | None = None
    votes: list[VoteResponseSchema] | None = None

class UpdateProposalSchema(BaseModel):

    author_id: int
    title: str | None = Field(None, min_length=2, max_length=50)
    description: str | None = Field(None, min_length=2, max_length=500)
    deadline: datetime | None = None

class ProposalResultSchema(BaseModel):

    status: ProposalStatus

class StartProposalSchema(BaseModel):

    author_id: int

class FinishProposalSchema(BaseModel):

    author_id: int

class DeleteProposalSchema(BaseModel):

    author_id: int