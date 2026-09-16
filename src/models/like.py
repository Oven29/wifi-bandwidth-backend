from sqlalchemy import Column, Integer, ForeignKey

from src.db.base import Base


class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    activity_id = Column(Integer, ForeignKey(
        "network_activities.id"), nullable=False)
