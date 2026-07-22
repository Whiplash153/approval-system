from datetime import datetime

from app.repositories.user_repository import UserRepo
from app.repositories.vote_repository import VoteRepo
from app.repositories.proposal_repository import ProposalRepo
from app.repositories.participant_repository import ParticipantRepo
from app.repositories.audit_log_repository import AuditLogRepo

from app.models.proposal import Proposal
from app.models.vote import Vote
from app.models.participant import Participant
from app.models.audit import AuditLog

from sqlalchemy.orm import Session

from app.models.enums import ProposalStatus
from app.core.errors import (
    ProposalNotFoundError,
    NotParticipantError,
    AlreadyVotedError,
    InvalidProposalStatusError,
    NotAuthorError,
    UserNotFoundError,
    EmptyParticipantsError,
    DuplicateParticipantsError,
    VoteNotFoundError
)

class ProposalService:
    def __init__(self, session: Session):
        self.session = session
        self.proposal_repo = ProposalRepo(session)
        self.user_repo = UserRepo(session)
        self.vote_repo = VoteRepo(session)
        self.participant_repo = ParticipantRepo(session)
        self.audit_repo = AuditLogRepo(session)

# ======= INTERNAL HELPERS ========
# =================================

    def _log_action(self, proposal_id, user_id, action):

        new_log = AuditLog(
            proposal_id=proposal_id,
            user_id=user_id,
            action=action
        )
        self.audit_repo.create(new_log)

    def _maybe_finish(self, proposal):

        #ALL VOTED CHECK
        if self.vote_repo.votes_count(proposal.id) == self.participant_repo.participants_count(proposal.id):
            self._finish_proposal(proposal.id, action="auto_finish(all_voted)")
            return

        #DEADLINE CHECK
        if proposal.deadline:
            if datetime.utcnow() > proposal.deadline:
                self._finish_proposal(proposal.id, action="auto_finish(deadline)")
                return

    def _finish_proposal(self, proposal_id, action):

        #FIND PROPOSAL (LOCKED!)
        proposal = self.proposal_repo.locked_get_by_id(proposal_id)
        if not proposal:
            raise ProposalNotFoundError

        # STATUS CHECK
        if proposal.status != ProposalStatus.VOTING:
            raise InvalidProposalStatusError

        # APPROVE OR REJECT FINAL STATUS CHOOSE
        votes = self.vote_repo.get_by_proposal_id(proposal_id)

        status_upd = self._calculate_result(votes)

        self._status_changer(proposal, status_upd)

        #LOG
        self._log_action(
            proposal_id=proposal.id,
            user_id=proposal.author_id,
            action=action
        )

    def _calculate_result(self, votes):

        approve_count = 0
        reject_count = 0
        for vote in votes:
            if vote.value == "approve":
                approve_count += 1
            else:
                reject_count += 1

        # SET PROPOSAL STATUS
        if approve_count > reject_count:
            return ProposalStatus.APPROVED
        else:
            return ProposalStatus.REJECTED

    def _status_changer(self, proposal, new_status):

        allowed_transitions = {
            ProposalStatus.DRAFT: [ProposalStatus.VOTING, ProposalStatus.DELETED],
            ProposalStatus.VOTING: [ProposalStatus.APPROVED, ProposalStatus.REJECTED, ProposalStatus.DELETED],
            ProposalStatus.APPROVED: [ProposalStatus.DELETED],
            ProposalStatus.REJECTED: [ProposalStatus.DELETED],
            ProposalStatus.DELETED: [],
        }

        current_status = proposal.status

        if new_status not in allowed_transitions[current_status]:
            raise InvalidProposalStatusError

        proposal.status = new_status

# ======= PROPOSAL LIFECYCLE ========
# ===================================

    def create_proposal(self, title, description, author_id, participant_ids,
                        deadline = None):

        #AUTHOR CHECK
        author = self.user_repo.get_by_id(author_id)
        if not author:
            raise UserNotFoundError

        #PARTICIPANT_IDS CHECK
        if not participant_ids:
            raise EmptyParticipantsError

        if len(participant_ids) != len(set(participant_ids)):
            raise DuplicateParticipantsError

        participants_list = []
        for participant_id in participant_ids:
            user = self.user_repo.get_by_id(participant_id)
            if not user:
                raise UserNotFoundError
            participants_list.append(user)

        #CREATE PROPOSAL
        new_proposal = Proposal(
            title=title,
            description=description,
            author_id=author_id,
            status=ProposalStatus.DRAFT,
            deadline=deadline
        )

        #ADD PROPOSAL
        self.proposal_repo.add(new_proposal)
        
        #GET PROPOSAL ID
        self.session.flush()

        #CREATE PARTICIPANTS
        for user in participants_list:
            participant = Participant(
                proposal_id=new_proposal.id,
                user_id=user.id
            )
            self.participant_repo.add(participant)

        #LOG
        self._log_action(
            proposal_id=new_proposal.id,
            user_id=author_id,
            action="create_proposal"
        )

        #COMMIT, REFRESH AND RETURN PROPOSAL
        self.session.commit()
        self.session.refresh(new_proposal)
        return new_proposal

    def start_voting(self, proposal_id, author_id):

        #FIND PROPOSAL (LOCKED!)
        proposal = self.proposal_repo.locked_get_by_id(proposal_id)
        if not proposal:
            raise ProposalNotFoundError

        #AUTHOR CHECK
        if proposal.author_id != author_id:
            raise NotAuthorError

        #STATUS CHECK
        if proposal.status != ProposalStatus.DRAFT:
            raise InvalidProposalStatusError

        #STATUS CHANGE
        self._status_changer(proposal, ProposalStatus.VOTING)

        #LOG
        self._log_action(
            proposal_id=proposal.id,
            user_id=author_id,
            action="start_voting"
        )

        #COMMIT, REFRESH AND RETURN PROPOSAL
        self.session.commit()
        self.session.refresh(proposal)
        return proposal

    def delete_proposal(self, proposal_id, author_id):

        #FIND PROPOSAL (LOCKED!)
        proposal = self.proposal_repo.locked_get_by_id(proposal_id)
        if not proposal:
            raise ProposalNotFoundError

        #AUTHOR CHECK
        if proposal.author_id != author_id:
            raise NotAuthorError

        #DELETE (+STATUS CHECK)
        self._status_changer(proposal, ProposalStatus.DELETED)

        #LOG
        self._log_action(
            proposal_id=proposal.id,
            user_id=author_id,
            action="delete_proposal"
        )

        #COMMIT AND RETURN PROPOSAL
        self.session.commit()
        return proposal

    def manual_finish(self, proposal_id, author_id):

        #FIND PROPOSAL (LOCKED!)
        proposal = self.proposal_repo.locked_get_by_id(proposal_id)
        if not proposal:
            raise ProposalNotFoundError

        #AUTHOR CHECK
        if proposal.author_id != author_id:
            raise NotAuthorError

        #STATUS CHECK
        if proposal.status != ProposalStatus.VOTING:
            raise InvalidProposalStatusError

        #FINISH PROPOSAL
        self._finish_proposal(proposal.id, action="manual_finish")

        self.session.commit()
        return proposal

    def update_proposal(self, proposal_id, author_id,
                        title=None, description=None, deadline=None):

        #FIND PROPOSAL (LOCKED!)
        proposal = self.proposal_repo.locked_get_by_id(proposal_id)
        if not proposal:
            raise ProposalNotFoundError

        #AUTHOR CHECK
        if proposal.author_id != author_id:
            raise NotAuthorError

        #STATUS CHECK
        if proposal.status != ProposalStatus.DRAFT:
            raise InvalidProposalStatusError

        #UPDATE
        if title is not None:
            proposal.title = title

        if description is not None:
            proposal.description = description

        if deadline is not None:
            proposal.deadline = deadline

        #LOG
        self._log_action(
            proposal_id=proposal.id,
            user_id=author_id,
            action="update_proposal"
        )

        #COMMIT AND RETURN PROPOSAL
        self.session.commit()
        return proposal

# ======= VOTE OPERATIONS ========
# ================================

    def change_vote(self, proposal_id, user_id, value):

        # FIND PROPOSAL (LOCKED!)
        proposal = self.proposal_repo.locked_get_by_id(proposal_id)
        if not proposal:
            raise ProposalNotFoundError

        # IS USER PARTICIPANT
        participant = self.participant_repo.get_by_user_and_proposal(
            user_id,
            proposal_id
        )
        if not participant:
            raise NotParticipantError

        # EXISTING VOTE CHECK
        existing_vote = self.vote_repo.get_by_user_and_proposal(
            user_id,
            proposal_id
        )
        if not existing_vote:
            raise VoteNotFoundError

        # STATUS CHECK
        if proposal.status != ProposalStatus.VOTING:
            raise InvalidProposalStatusError

        # DEADLINE CHECK
        if proposal.deadline and datetime.utcnow() > proposal.deadline:
            raise InvalidProposalStatusError

        # CHANGE VOTE
        existing_vote.value = value

        self.session.flush()

        #LOG
        self._log_action(
            proposal_id=proposal.id,
            user_id=user_id,
            action="change_vote"
        )

        # FINISH CHECK
        self._maybe_finish(proposal)

        self.session.commit()
        return existing_vote

    def create_vote(self, proposal_id, user_id, value):

        #FIND PROPOSAL (LOCKED!)
        proposal = self.proposal_repo.locked_get_by_id(proposal_id)
        if not proposal:
            raise ProposalNotFoundError

        #IS USER PARTICIPANT
        participant = self.participant_repo.get_by_user_and_proposal(user_id, proposal_id)
        if not participant:
            raise NotParticipantError

        #VOTE MADE CHECK
        existing_vote = self.vote_repo.get_by_user_and_proposal(user_id, proposal_id)
        if existing_vote:
            raise AlreadyVotedError

        #STATUS CHECK
        if proposal.status != ProposalStatus.VOTING:
            raise InvalidProposalStatusError

        #DEADLINE CHECK
        if proposal.deadline and datetime.utcnow() > proposal.deadline:
            raise InvalidProposalStatusError

        #CREATE VOTE
        new_vote = Vote(
            proposal_id=proposal_id,
            user_id=user_id,
            value=value
        )

        #SAVE VOTE
        self.vote_repo.add(new_vote)
        self.session.flush()

        #LOG
        self._log_action(
            proposal_id=proposal.id,
            user_id=user_id,
            action="create_vote"
        )

        #FINISH CHECK
        self._maybe_finish(proposal)

        self.session.commit()
        return new_vote

# ======= READ METHODS ========
# =============================

    def get_proposal(self, proposal_id):

        #FIND PROPOSAL
        proposal = self.proposal_repo.get_by_id(proposal_id)
        if not proposal:
            raise ProposalNotFoundError

        return proposal

    def get_proposal_votes(self, proposal_id):

        #FIND PROPOSAL
        proposal = self.proposal_repo.get_by_id(proposal_id)
        if not proposal:
            raise ProposalNotFoundError

        proposal_votes = self.vote_repo.get_by_proposal_id(proposal_id)
        return proposal_votes

    def get_proposal_participants(self, proposal_id):

        #FIND PROPOSAL
        proposal = self.proposal_repo.get_by_id(proposal_id)
        if not proposal:
            raise ProposalNotFoundError

        proposal_participants = self.participant_repo.get_by_proposal_id(proposal_id)
        return proposal_participants

    def get_proposal_with_votes(self, proposal_id):

        #FIND PROPOSAL
        proposal = self.proposal_repo.get_with_votes(proposal_id)
        if not proposal:
            raise ProposalNotFoundError

        return proposal






