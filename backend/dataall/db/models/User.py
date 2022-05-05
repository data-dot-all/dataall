from sqlalchemy import Column, String

from .. import Base, utils


class User(Base):
    __tablename__ = "user"
    userId = Column(String, primary_key=True, default=utils.uuid("user"))
    userName = Column(String, nullable=False)
