import pytest

from datetime import datetime, timedelta

from app.services.proposal_service import ProposalService
from app.models.user import User

from app.repositories.user_repository import UserRepo
from app.repositories.vote_repository import VoteRepo
from app.repositories.proposal_repository import ProposalRepo

from app.models.enums import ProposalStatus

from app.core.errors import (
    DuplicateParticipantsError,
    EmptyParticipantsError,
    AlreadyVotedError,
    NotParticipantError,
    InvalidProposalStatusError,
    ProposalNotFoundError,
    VoteNotFoundError
)

# ===== HELPERS =====
# ===================

def _create_one_user(session):

    user1 = User()
    user1.name = "A"
    user1.email = "a@test.com"

    session.add(user1)
    session.commit()

    return user1

def _create_two_users(session):

    user1 = User()
    user1.name = "A"
    user1.email = "a@test.com"

    user2 = User()
    user2.name = "B"
    user2.email = "b@test.com"

    session.add_all([user1, user2])
    session.commit()

    return user1, user2

def _create_three_users(session):

    user1 = User()
    user1.name = "A"
    user1.email = "a@test.com"

    user2 = User()
    user2.name = "B"
    user2.email = "b@test.com"

    user3 = User()
    user3.name = "C"
    user3.email = "c@test.com"

    session.add_all([user1, user2, user3])
    session.commit()

    return user1, user2, user3

# ==== VOTE TESTS ====
# ====================

def test_create_vote(session):

    #SETUP USERS
    user1, user2 = _create_two_users(session)

    #SETUP PROPOSAL
    service = ProposalService(session)
    proposal = service.create_proposal("open window", "yo", user1.id,
                                       [user1.id, user2.id])

    service.start_voting(proposal.id, user1.id)

    #TEST
    service.create_vote(proposal.id, user1.id, "approve")

    vote_repo = VoteRepo(session)
    the_vote = vote_repo.get_by_user_and_proposal(user_id=user1.id, proposal_id=proposal.id)

    assert the_vote.user_id == user1.id
    assert the_vote.proposal_id == proposal.id
    assert the_vote.value == "approve"

def test_create_vote_duplicate(session):

    #SETUP USERS
    user1, user2 = _create_two_users(session)

    #SETUP PROPOSAL
    service = ProposalService(session)
    proposal = service.create_proposal("open window", "yo", user1.id,
                                       [user1.id, user2.id])

    service.start_voting(proposal.id, user1.id)

    #TEST
    service.create_vote(proposal.id, user1.id, "approve")
    with pytest.raises(AlreadyVotedError):
        service.create_vote(proposal.id, user1.id, "approve")

def test_create_vote_not_participant(session):

    #SETUP USERS
    user1, user2 = _create_two_users(session)

    #SETUP PROPOSAL
    service = ProposalService(session)
    proposal = service.create_proposal("open window", "yo", user1.id,
                                       [user1.id])

    service.start_voting(proposal.id, user1.id)

    #TEST
    with pytest.raises(NotParticipantError):
        service.create_vote(proposal.id, user2.id, "approve")

def test_create_vote_invalid_status(session):

    #SETUP USERS
    user1, user2 = _create_two_users(session)

    #SETUP PROPOSAL
    service = ProposalService(session)
    proposal = service.create_proposal("open window", "yo", user1.id,
                                       [user1.id, user2.id])

    #TEST
    with pytest.raises(InvalidProposalStatusError):
        service.create_vote(proposal.id, user2.id, "approve")

def test_change_vote(session):

    #SETUP USERS
    user1, user2 = _create_two_users(session)

    #SETUP PROPOSAL
    service = ProposalService(session)
    proposal = service.create_proposal("open window", "yo", user1.id,
                                       [user1.id, user2.id])

    service.start_voting(proposal.id, user1.id)

    #TEST
    service.create_vote(proposal.id, user1.id, "approve")
    service.change_vote(proposal.id, user1.id, "reject")

    vote_repo = VoteRepo(session)
    the_vote = vote_repo.get_by_user_and_proposal(user_id=user1.id, proposal_id=proposal.id)

    assert the_vote.user_id == user1.id
    assert the_vote.proposal_id == proposal.id
    assert the_vote.value == "reject"

def test_change_vote_not_found(session):

    #SETUP USERS
    user1, user2 = _create_two_users(session)

    #SETUP PROPOSAL
    service = ProposalService(session)
    proposal = service.create_proposal("open window", "yo", user1.id,
                                       [user1.id, user2.id])

    #TEST
    with pytest.raises(VoteNotFoundError):
        service.change_vote(proposal.id, user2.id, "approve")

def test_change_vote_invalid_status(session):

    #SETUP USERS
    user1, user2 = _create_two_users(session)

    #SETUP PROPOSAL
    service = ProposalService(session)
    proposal = service.create_proposal("open window", "yo", user1.id,
                                       [user1.id, user2.id])

    service.start_voting(proposal.id, user1.id)

    #TEST
    service.create_vote(proposal.id, user1.id, "approve")
    service.create_vote(proposal.id, user2.id, "approve")

    #TEST
    with pytest.raises(InvalidProposalStatusError):
        service.change_vote(proposal.id, user1.id, "reject")

# ==== PROPOSAL TESTS ====
# ========================

def test_create_user(session):

    #SETUP
    user = _create_one_user(session)

    #TEST
    user_repo = UserRepo(session)
    the_user = user_repo.get_by_id(user.id)

    assert the_user.name == "A"
    assert the_user.email == "a@test.com"

def test_create_proposal(session):

    #SETUP
    user1, user2, user3 = _create_three_users(session)

    #TEST
    service = ProposalService(session)
    proposal = service.create_proposal("proposal_test", "good", user1.id,
                            [user1.id, user2.id, user3.id])

    assert proposal.title == "proposal_test"
    assert proposal.description == "good"
    assert proposal.author_id == user1.id
    assert proposal.status == ProposalStatus.DRAFT

    actual_ids = [participant.user_id for participant in proposal.participants]
    expected_ids = [user1.id, user2.id, user3.id]
    assert set(actual_ids) == set(expected_ids)

def test_proposal_duplicate_error(session):

    #SETUP
    user1, user2 = _create_two_users(session)

    #TEST
    service = ProposalService(session)
    with pytest.raises(DuplicateParticipantsError):
        service.create_proposal("proposal_test", "good", user1.id,
                                [user1.id, user2.id, user2.id])

def test_proposal_participants_empty(session):

    #SETUP
    user = _create_one_user(session)

    #TEST
    service = ProposalService(session)
    with pytest.raises(EmptyParticipantsError):
        service.create_proposal("proposal_test", "good", user.id,[])

def test_proposal_not_found(session):

    #SETUP USERS
    user1, user2 = _create_two_users(session)

    service = ProposalService(session)

    #TEST
    with pytest.raises(ProposalNotFoundError):
        service.create_vote(999, user1.id, "reject")

def test_update_draft_proposal(session):

    #SETUP
    user1, user2, user3 = _create_three_users(session)

    #SETUP PROPOSAL
    service = ProposalService(session)
    proposal = service.create_proposal("proposal_test", "good", user1.id,
                            [user1.id, user2.id, user3.id])

    assert proposal.title == "proposal_test"
    assert proposal.description == "good"
    assert proposal.author_id == user1.id
    assert proposal.status == ProposalStatus.DRAFT

    service.update_proposal(proposal.id, user1.id, title="proposal_test2")

    assert proposal.title == "proposal_test2"
    assert proposal.description == "good"
    assert proposal.author_id == user1.id
    assert proposal.status == ProposalStatus.DRAFT

def test_update_voting_proposal(session):

    #SETUP USERS
    user1, user2 = _create_two_users(session)

    #SETUP PROPOSAL
    service = ProposalService(session)
    proposal = service.create_proposal("open window", "yo", user1.id,
                                       [user1.id, user2.id])

    #TEST
    service.start_voting(proposal.id, user1.id)

    with pytest.raises(InvalidProposalStatusError):
        service.update_proposal(proposal.id, user1.id, title="proposal_test2")

def test_delete_draft_proposal(session):

    #SETUP
    user1, user2, user3 = _create_three_users(session)

    #SETUP PROPOSAL
    service = ProposalService(session)
    proposal = service.create_proposal("proposal_test", "good", user1.id,
                            [user1.id, user2.id, user3.id])

    assert proposal.title == "proposal_test"
    assert proposal.description == "good"
    assert proposal.author_id == user1.id
    assert proposal.status == ProposalStatus.DRAFT

    service.delete_proposal(proposal.id, user1.id)

    with pytest.raises(ProposalNotFoundError):
        service.get_proposal(proposal.id)

def test_delete_approved_proposal(session):

    #SETUP USERS
    user1, user2 = _create_two_users(session)

    #SETUP PROPOSAL
    service = ProposalService(session)
    proposal = service.create_proposal("open window", "yo", user1.id,
                                       [user1.id, user2.id])

    #TEST
    service.start_voting(proposal.id, user1.id)

    service.create_vote(proposal.id, user1.id, "approve")
    service.create_vote(proposal.id, user2.id, "approve")

    assert proposal.status == ProposalStatus.APPROVED

    service.delete_proposal(proposal.id, user1.id)

    with pytest.raises(ProposalNotFoundError):
        service.get_proposal(proposal.id)

# ===== FINISH TESTS =====
# ========================

def test_auto_finish_proposal(session):

    #SETUP USERS
    user1, user2 = _create_two_users(session)

    #SETUP PROPOSAL
    service = ProposalService(session)
    proposal = service.create_proposal("open window", "yo", user1.id,
                                       [user1.id, user2.id])

    service.start_voting(proposal.id, user1.id)

    #TEST
    service.create_vote(proposal.id, user1.id, "approve")
    service.create_vote(proposal.id, user2.id, "approve")

    proposal_repo = ProposalRepo(session)
    the_proposal = proposal_repo.get_by_id(proposal_id=proposal.id)

    assert the_proposal.status == ProposalStatus.APPROVED

def test_auto_finish_rejected(session):

    #SETUP USERS
    user1, user2 = _create_two_users(session)

    #SETUP PROPOSAL
    service = ProposalService(session)
    proposal = service.create_proposal("open window", "yo", user1.id,
                                       [user1.id, user2.id])

    service.start_voting(proposal.id, user1.id)

    #TEST
    service.create_vote(proposal.id, user1.id, "reject")
    service.create_vote(proposal.id, user2.id, "reject")

    proposal_repo = ProposalRepo(session)
    the_proposal = proposal_repo.get_by_id(proposal_id=proposal.id)

    assert the_proposal.status == ProposalStatus.REJECTED

def test_manual_finish_proposal(session):

    #SETUP USERS
    user1, user2 = _create_two_users(session)

    #SETUP PROPOSAL
    service = ProposalService(session)
    proposal = service.create_proposal("open window", "yo", user1.id,
                                       [user1.id, user2.id])

    service.start_voting(proposal.id, user1.id)

    #START TEST
    service.create_vote(proposal.id, user1.id, "reject")

    proposal_repo = ProposalRepo(session)
    the_proposal = proposal_repo.get_by_id(proposal_id=proposal.id)

    assert the_proposal.status == ProposalStatus.VOTING

    #MANUAL FINISH
    service.manual_finish(the_proposal.id, user1.id)

    proposal_repo = ProposalRepo(session)
    the_proposal_2 = proposal_repo.get_by_id(proposal_id=proposal.id)

    assert the_proposal_2.status == ProposalStatus.REJECTED

def test_manual_finish_invalid_status(session):

    #SETUP USERS
    user1, user2 = _create_two_users(session)

    #SETUP PROPOSAL
    service = ProposalService(session)
    proposal = service.create_proposal("open window", "yo", user1.id,
                                       [user1.id, user2.id])

    service.start_voting(proposal.id, user1.id)

    #START TEST
    service.create_vote(proposal.id, user1.id, "reject")
    service.create_vote(proposal.id, user2.id, "reject")

    proposal_repo = ProposalRepo(session)
    the_proposal = proposal_repo.get_by_id(proposal_id=proposal.id)

    assert the_proposal.status == ProposalStatus.REJECTED

    #MANUAL FINISH

    with pytest.raises(InvalidProposalStatusError):
        service.manual_finish(the_proposal.id, user1.id)

# ===== DEADLINE TESTS =====
# ==========================

def test_deadline_auto_finish(session):

    #SETUP USERS
    user1, user2 = _create_two_users(session)

    #SETUP EXPIRED PROPOSAL
    service = ProposalService(session)
    proposal = service.create_proposal("open window",
                                       "yo",
                                       user1.id,
                                       [user1.id, user2.id],
                                       deadline=datetime.utcnow() - timedelta(minutes=1))

    service.start_voting(proposal.id, user1.id)

    assert proposal.status == ProposalStatus.VOTING

    #START TEST
    with pytest.raises(InvalidProposalStatusError):
        service.create_vote(proposal.id, user1.id, "approve")






















