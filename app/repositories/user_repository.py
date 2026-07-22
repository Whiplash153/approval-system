from sqlalchemy.orm import Session
from app.models.user import User

class UserRepo:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, user_id):
        result = self.session.query(User).filter(User.id == user_id).first()
        return result

    def add(self, user: User):
        self.session.add(user)