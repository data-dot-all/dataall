from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import query_expression
from sqlalchemy.dialects import postgresql

from .. import Base, Resource, utils


class DataPipelineEnvironment(Base, Resource):
    __tablename__ = 'datapipelineenvironments'
    envPipelineUri = Column(String, nullable=False, primary_key=True)
    environmentUri = Column(String, nullable=False)
    environmentLabel = Column(String, nullable=False)
    pipelineUri = Column(String, nullable=False)
    pipelineLabel = Column(String, nullable=False)
    stage = Column(String, nullable=False)
    order = Column(Integer, nullable=False)
    region = Column(String, default='eu-west-1')
    AwsAccountId = Column(String, nullable=False)
    samlGroupName = Column(String, nullable=False)
