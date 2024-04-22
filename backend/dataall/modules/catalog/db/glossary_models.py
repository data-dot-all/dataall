import enum
from datetime import datetime

from sqlalchemy import Boolean, Column, String, DateTime, Enum
from sqlalchemy.orm import query_expression

from dataall.base.db import Base
from dataall.base.db import utils


class GlossaryNodeStatus(enum.Enum):
    draft = 'draft'
    approved = 'approved'
    expired = 'expired'
    alert = 'alert'
    archived = 'archived'


class GlossaryNode(Base):
    __tablename__ = 'glossary_node'
    nodeUri = Column(String, primary_key=True, default=utils.uuid('glossary_node'))
    parentUri = Column(String, nullable=True)
    nodeType = Column(String, default='G')
    status = Column(String, Enum(GlossaryNodeStatus), default=GlossaryNodeStatus.draft.value)
    path = Column(String, nullable=False)
    label = Column(String, nullable=False)
    readme = Column(String, nullable=False)
    created = Column(DateTime, default=datetime.now)
    updated = Column(DateTime, nullable=True, onupdate=datetime.now)
    deleted = Column(DateTime, nullable=True)
    owner = Column(String, nullable=False)
    admin = Column(String, nullable=True)
    isLinked = query_expression()
    isMatch = query_expression()


class TermLink(Base):
    __tablename__ = 'term_link'
    linkUri = Column(String, primary_key=True, default=utils.uuid('term_link'))
    nodeUri = Column(String, nullable=False)
    targetUri = Column(String, nullable=False)
    targetType = Column(String, nullable=False)
    approvedBySteward = Column(Boolean, default=False)
    approvedByOwner = Column(Boolean, default=False)
    owner = Column(String, nullable=False)
    created = Column(DateTime, default=datetime.now)
    updated = Column(DateTime, nullable=True, onupdate=datetime.now)
    deleted = Column(DateTime, nullable=True)
    path = query_expression()
    label = query_expression()
    readme = query_expression()
