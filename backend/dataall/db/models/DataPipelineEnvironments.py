from sqlalchemy import Column, String
from sqlalchemy.orm import query_expression
from sqlalchemy.dialects import postgresql

from .. import Base, Resource, utils


class DataPipelineEnvironment(Resource, Base):
    __tablename__ = 'datapipelineenvironments'
    envPipelineUri = Column(String, nullable=False, primary_key=True)
    environmentUri = Column(String, nullable=False)
    environmentLabel = Column(String, nullable=False)
    pipelineUri = Column(String, nullable=False)
    pipelineLabel = Column(String, nullable=False)
    stage = Column(String, nullable=False)
    region = Column(String, default='eu-west-1')
    AwsAccountId = Column(String, nullable=False)
    SamlGroupName = Column(String, nullable=False)
