from typing import Optional
from sqlalchemy import Column, String, Boolean

from dataall.base.db import Base


class ResourceLock(Base):
    __tablename__ = 'resource_lock'

    resourceUri = Column(String, nullable=False, primary_key=True)
    resourceType = Column(String, nullable=False, primary_key=True)
    acquiredByUri = Column(String, nullable=True)
    acquiredByType = Column(String, nullable=True)

    def __init__(
        self,
        resourceUri: str,
        resourceType: str,
        acquiredByUri: Optional[str] = None,
        acquiredByType: Optional[str] = None,
    ):
        self.resourceUri = resourceUri
        self.resourceType = resourceType
        self.acquiredByUri = acquiredByUri
        self.acquiredByType = acquiredByType
