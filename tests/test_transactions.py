import threading

from app.services.proposal_service import ProposalService
from app.models.enums import ProposalStatus
from tests.reserve_db_session import SessionLocal

from app.models.vote import Vote
from app.models.participant import Participant
from app.models.proposal import Proposal
from app.models.user import User
from app.models.audit import AuditLog

#CLEAR DB
def _clear_db():
    session = SessionLocal()

    session.query(AuditLog).delete()
    session.query(Vote).delete()
    session.query(Participant).delete()
    session.query(Proposal).delete()
    session.query(User).delete()

    session.commit()
    session.close()

def test_same_time_voting():

    session = SessionLocal()

    #CLEAR DB
    _clear_db()

    #SETUP USERS
    user1 = User()
    user1.name = "Andy"
    user1.email = "andy@test.com"

    user2 = User()
    user2.name = "Bruce"
    user2.email = "bruce@test.com"

    session.add_all([user1, user2])
    session.commit()

    #SETUP PROPOSAL
    service = ProposalService(session)
    proposal = service.create_proposal("proposal_test", "good", user1.id,
                            [user1.id, user2.id])

    #SAVE FLOW DATA
    proposal_id = proposal.id
    user1_id = user1.id
    user2_id = user2.id

    #TEST
    service.start_voting(proposal_id, user1_id)

    session.close()

    def make_vote(user_id, value):

        #SETUP
        session = SessionLocal()
        service = ProposalService(session)

        service.create_vote(proposal_id, user_id, value)

        session.close()

    #THREADS
    thread1 = threading.Thread(
        target=make_vote,
        args=(user1_id, "approve")
    )

    thread2 = threading.Thread(
        target=make_vote,
        args=(user2_id, "approve")
    )

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()

    #VERIFICATION
    session = SessionLocal()
    service = ProposalService(session)

    the_proposal = service.get_proposal(proposal_id=proposal_id)
    votes = service.vote_repo.get_by_proposal_id(proposal_id=the_proposal.id)

    assert len(votes) == 2
    assert the_proposal.status == ProposalStatus.APPROVED

    session.close()
