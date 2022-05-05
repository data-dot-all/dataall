import datetime

from sqlalchemy import Column, DateTime, String, Boolean

from .. import Base


class RedshiftClusterDatasetTable(Base):
    __tablename__ = "redshiftcluster_datasettable"
    clusterUri = Column(String, nullable=False, primary_key=True)
    datasetUri = Column(String, nullable=False, primary_key=True)
    tableUri = Column(String, nullable=False, primary_key=True)
    shareUri = Column(String)
    enabled = Column(Boolean, default=False)
    schema = Column(String, nullable=False)
    databaseName = Column(String, nullable=False)
    dataLocation = Column(String, nullable=True)
    created = Column(DateTime, default=datetime.datetime.now)
    updated = Column(DateTime, onupdate=datetime.datetime.now)
    deleted = Column(DateTime)
