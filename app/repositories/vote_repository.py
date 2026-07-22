from sqlalchemy.orm import Session
from app.models.vote import Vote

class VoteRepo:
    def __init__(self, session: Session):
        self.session = session

    def add(self, vote: Vote):
        self.session.add(vote)

    def get_by_proposal_id(self, proposal_id):
        result = self.session.query(Vote).filter(Vote.proposal_id == proposal_id).all()
        return result

    def get_by_user_and_proposal(self, user_id, proposal_id):
        result = self.session.query(Vote).filter(Vote.user_id == user_id,
                                                 Vote.proposal_id == proposal_id).first()
        return result

    def votes_count(self, proposal_id):
        result = self.session.query(Vote).filter(Vote.proposal_id == proposal_id).count()
        return result