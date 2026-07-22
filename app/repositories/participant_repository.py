from sqlalchemy.orm import Session
from app.models.participant import Participant

class ParticipantRepo:
    def __init__(self, session: Session):
        self.session = session

    def add(self, participant: Participant):
        self.session.add(participant)

    def get_by_proposal_id(self, proposal_id):
        result = self.session.query(Participant).filter(Participant.proposal_id == proposal_id).all()
        return result

    def get_by_user_and_proposal(self, user_id, proposal_id):
        result = self.session.query(Participant).filter(Participant.user_id == user_id,
                                                 Participant.proposal_id == proposal_id).first()
        return result

    def participants_count(self, proposal_id):
        result = self.session.query(Participant).filter(Participant.proposal_id == proposal_id).count()
        return result
