from sqlalchemy import Column, String
from sqlalchemy.orm import query_expression
from enum import Enum

from backend.db import Base, Resource, utils

class DataPipelineRole(Enum):
    Creator = '999'
    Admin = '900'
    NoPermission = '000'

class DataPipeline(Resource, Base):
    __tablename__ = 'datapipeline'
    environmentUri = Column(String, nullable=False)
    DataPipelineUri = Column(
        String, nullable=False, primary_key=True, default=utils.uuid('DataPipelineUri')
    )
    region = Column(String, default='eu-west-1')
    AwsAccountId = Column(String, nullable=False)
    SamlGroupName = Column(String, nullable=False)
    repo = Column(String, nullable=False)
    devStrategy = Column(String, nullable=False)
    template = Column(String, nullable=True, default="")
    userRoleForPipeline = query_expression()
