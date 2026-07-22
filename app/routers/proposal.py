from fastapi import APIRouter, Depends
from app.services.proposal_service import ProposalService
from app.db.session import get_db

from app.schemas.proposal import (
    ProposalCreateSchema,
    ProposalResponseSchema,
    ProposalResultSchema,
    StartProposalSchema,
    FinishProposalSchema,
    UpdateProposalSchema,
    DeleteProposalSchema
)
from app.schemas.vote import VoteCreateSchema, VoteResponseSchema

router = APIRouter()

# ==== HELPERS ====
# =================

def proposal_response_schema(proposal, votes=None):

    vote_schemas = None

    if votes:
        vote_schemas = [
            VoteResponseSchema(
                id=vote.id,
                proposal_id=vote.proposal_id,
                user_id=vote.user_id,
                value=vote.value,
                status=proposal.status
            )
            for vote in votes
        ]

    return ProposalResponseSchema(
        id=proposal.id,
        title=proposal.title,
        description=proposal.description,
        author_id=proposal.author_id,
        status=proposal.status,
        created_at=proposal.created_at,
        deadline=proposal.deadline,
        votes=vote_schemas
    )

# ==== PROPOSAL READ ENDPOINTS ======
# ===================================

@router.get("/proposals/{proposal_id}", response_model=ProposalResponseSchema)
def get_proposal_by_id(proposal_id, session = Depends(get_db)):

    service = ProposalService(session)
    proposal = service.get_proposal(proposal_id=proposal_id)

    return proposal_response_schema(proposal)

@router.get("/proposals/{proposal_id}/result", response_model=ProposalResultSchema)
def get_proposal_result(proposal_id, session = Depends(get_db)):

    service = ProposalService(session)
    proposal = service.get_proposal(proposal_id=proposal_id)

    return ProposalResultSchema(
        status=proposal.status
    )

@router.get("/proposals/{proposal_id}/votes", response_model=ProposalResponseSchema)
def get_proposal_with_votes(proposal_id, session = Depends(get_db)):

    service = ProposalService(session)
    proposal = service.get_proposal_with_votes(proposal_id=proposal_id)

    return proposal_response_schema(proposal, votes=proposal.votes)

# ==== PROPOSAL WRITE ENDPOINTS =====
# ===================================

@router.post("/proposals", response_model=ProposalResponseSchema)
def create_proposal(data: ProposalCreateSchema, session = Depends(get_db)):

    service = ProposalService(session)
    proposal = service.create_proposal(data.title, data.description,
                                       data.author_id, data.participant_ids, data.deadline)

    return proposal_response_schema(proposal)

@router.delete("/proposals/{proposal_id}", response_model=ProposalResponseSchema)
def delete_proposal(proposal_id, data: DeleteProposalSchema, session = Depends(get_db)):

    service = ProposalService(session)
    proposal = service.delete_proposal(proposal_id=proposal_id, author_id=data.author_id)

    return proposal_response_schema(proposal)

@router.post("/proposals/{proposal_id}/start", response_model=ProposalResponseSchema)
def start_proposal(proposal_id, data: StartProposalSchema, session = Depends(get_db)):

    service = ProposalService(session)
    proposal = service.start_voting(proposal_id=proposal_id, author_id=data.author_id)

    return proposal_response_schema(proposal)

@router.post("/proposals/{proposal_id}/finish", response_model=ProposalResponseSchema)
def finish_proposal(proposal_id, data: FinishProposalSchema, session = Depends(get_db)):

    service = ProposalService(session)
    proposal = service.manual_finish(proposal_id=proposal_id, author_id=data.author_id)

    return proposal_response_schema(proposal)

@router.patch("/proposals/{proposal_id}", response_model=ProposalResponseSchema)
def update_proposal(proposal_id, data: UpdateProposalSchema, session = Depends(get_db)):

    service = ProposalService(session)
    proposal = service.update_proposal(proposal_id=proposal_id,
                                       author_id=data.author_id,
                                       title=data.title,
                                       description=data.description,
                                       deadline=data.deadline)

    return proposal_response_schema(proposal)

# ==== VOTE ENDPOINTS ========
# ============================

@router.post("/votes", response_model=VoteResponseSchema)
def create_vote(data: VoteCreateSchema, session = Depends(get_db)):

    service = ProposalService(session)
    vote = service.create_vote(data.proposal_id, data.user_id, data.value)
    proposal = service.get_proposal(data.proposal_id)

    return VoteResponseSchema(
        id=vote.id,
        proposal_id=vote.proposal_id,
        user_id=vote.user_id,
        value=vote.value,
        status=proposal.status
    )

@router.patch("/votes", response_model=VoteResponseSchema)
def change_vote(data: VoteCreateSchema, session = Depends(get_db)):

    service = ProposalService(session)
    vote = service.change_vote(data.proposal_id, data.user_id, data.value)
    proposal = service.get_proposal(data.proposal_id)

    return VoteResponseSchema(
        id=vote.id,
        proposal_id=vote.proposal_id,
        user_id=vote.user_id,
        value=vote.value,
        status=proposal.status
    )