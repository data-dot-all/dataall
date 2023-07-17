from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import JSON

from .. import Base, Resource, utils


class DatasetQualityRule(Resource, Base):
    __tablename__ = 'dataset_quality_rule'
    datasetUri = Column(String, nullable=False)
    ruleUri = Column(String, primary_key=True, default=utils.uuid('dqlrule'))
    query = Column(String, nullable=False)
    status = Column(String, nullable=False, default='Created')
    logs = Column(JSON, default={})
