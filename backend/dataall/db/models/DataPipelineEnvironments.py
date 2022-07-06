from sqlalchemy import Column, String
from sqlalchemy.orm import query_expression
from sqlalchemy.dialects import postgresql

from .. import Base, Resource, utils


class DataPipelineEnvironments(Resource, Base):
    __tablename__ = 'datapipelineenvironments'
    environmentUri = Column(String, nullable=False)
    environmentLabel = Column(String, nullable=False)
    DataPipelineUri = Column(String, nullable=False)
    DataPipelineLabel = Column(String, nullable=False)
    envPipelineUri = Column(String, nullable=False, primary_key=True)
    region = Column(String, default='eu-west-1')
    AwsAccountId = Column(String, nullable=False)
    SamlGroupName = Column(String, nullable=False)
    devStage = Column(String, nullable=False)
