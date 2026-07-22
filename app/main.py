from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse

from app.routers.proposal import router
from app.core.errors import (
    ProposalNotFoundError,
    NotParticipantError,
    AlreadyVotedError,
    InvalidProposalStatusError,
    NotAuthorError,
    UserNotFoundError,
    InvalidVoteValueError,
    EmptyParticipantsError,
    DuplicateParticipantsError,
    VoteNotFoundError
)

app = FastAPI()
app.include_router(router)

#ERRORS MAPPING
@app.exception_handler(ProposalNotFoundError)
async def proposal_not_found_handler(request: Request, exc: ProposalNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": "Proposal not found"}
    )

@app.exception_handler(NotParticipantError)
async def not_participant_handler(request: Request, exc: NotParticipantError):
    return JSONResponse(
        status_code=403,
        content={"detail": "User is not a participant"}
    )

@app.exception_handler(AlreadyVotedError)
async def already_voted_handler(request: Request, exc: AlreadyVotedError):
    return JSONResponse(
        status_code=409,
        content={"detail": "User already voted"}
    )

@app.exception_handler(InvalidProposalStatusError)
async def invalid_proposal_status_handler(request: Request, exc: InvalidProposalStatusError):
    return JSONResponse(
        status_code=409,
        content={"detail": "Proposal in a wrong state"}
    )

@app.exception_handler(NotAuthorError)
async def not_author_handler(request: Request, exc: NotAuthorError):
    return JSONResponse(
        status_code=403,
        content={"detail": "Only author can perform this action"}
    )

@app.exception_handler(UserNotFoundError)
async def user_not_found_handler(request: Request, exc: UserNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": "User not found"}
    )

@app.exception_handler(InvalidVoteValueError)
async def invalid_vote_value_handler(request: Request, exc: InvalidVoteValueError):
    return JSONResponse(
        status_code=400,
        content={"detail": "Invalid vote value"}
    )

@app.exception_handler(EmptyParticipantsError)
async def empty_participants_error_handler(request: Request, exc: EmptyParticipantsError):
    return JSONResponse(
        status_code=400,
        content={"detail": "Participants list is empty"}
    )

@app.exception_handler(DuplicateParticipantsError)
async def duplicate_participants_handler(request: Request, exc: DuplicateParticipantsError):
    return JSONResponse(
        status_code=400,
        content={"detail": "Duplicate participants"}
    )

@app.exception_handler(VoteNotFoundError)
async def vote_not_found_error_handler(request: Request, exc: VoteNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": "Vote not found"}
    )
