import datetime

from sqlalchemy import Column, String, Boolean, DateTime

from dataall.base.db import Base, utils


class Vote(Base):
    __tablename__ = 'vote'
    voteUri = Column(String, primary_key=True, default=utils.uuid('vote'))
    username = Column(String, nullable=False)
    targetUri = Column(String, nullable=False)
    targetType = Column(String, nullable=False)
    upvote = Column(Boolean, nullable=True)
    created = Column(DateTime, default=datetime.datetime.now)
    updated = Column(DateTime, onupdate=datetime.datetime.now)

    def __repr__(self):
        if self.upvote:
            vote = 'Up'
        else:
            vote = 'Down'
        return f'<Vote - {vote}, from {self.username} for {self.targetType}//{self.targetUri}>'
