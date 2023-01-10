import datetime

from sqlalchemy import Column, DateTime, String, Boolean
from sqlalchemy.orm import query_expression

from .. import Base


class RedshiftClusterDataset(Base):
    __tablename__ = 'redshiftcluster_dataset'
    clusterUri = Column(String, nullable=False, primary_key=True)
    datasetUri = Column(String, nullable=False, primary_key=True)
    datasetCopyEnabled = Column(Boolean, default=True)
    created = Column(DateTime, default=datetime.datetime.now)
    updated = Column(DateTime, onupdate=datetime.datetime.now)
    deleted = Column(DateTime)
    userRoleForDataset = query_expression()
