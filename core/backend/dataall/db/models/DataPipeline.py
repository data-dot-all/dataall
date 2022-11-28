from sqlalchemy import Column, String
from sqlalchemy.orm import query_expression
from sqlalchemy.dialects import postgresql

from .. import Base, Resource, utils


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
