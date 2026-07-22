from sqlalchemy.orm import Session, joinedload
from app.models.proposal import Proposal
from app.models.enums import ProposalStatus

class ProposalRepo:
    def __init__(self, session: Session):
        self.session = session

    def add(self, proposal: Proposal):
        self.session.add(proposal)

    def get_by_id(self, proposal_id):
        result = self.session.query(Proposal).filter(
            Proposal.id == proposal_id,
            Proposal.status != ProposalStatus.DELETED).first()
        return result

    def get_by_id_include_deleted(self, proposal_id):
        result = self.session.query(Proposal).filter(Proposal.id == proposal_id).first()
        return result

    def get_with_votes(self, proposal_id):
        result = (self.session.query(Proposal).
                  options(joinedload(Proposal.votes)).
                  filter(Proposal.id == proposal_id,
                         Proposal.status != ProposalStatus.DELETED).
                  first())
        return result

    def locked_get_by_id(self, proposal_id):
        result = (self.session.query(Proposal).filter(Proposal.id == proposal_id,
                                                     Proposal.status != ProposalStatus.DELETED).
                  with_for_update().first())
        return result

    def delete(self, proposal):
        proposal.status = ProposalStatus.DELETED