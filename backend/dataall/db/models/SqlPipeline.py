from sqlalchemy import Column, String
from sqlalchemy.orm import query_expression

from .. import Base, Resource, utils


class SqlPipeline(Resource, Base):
    __tablename__ = "sqlpipeline"
    environmentUri = Column(String, nullable=False)
    sqlPipelineUri = Column(String, nullable=False, primary_key=True, default=utils.uuid("sqlPipelineUri"))
    region = Column(String, default="eu-west-1")
    AwsAccountId = Column(String, nullable=False)
    SamlGroupName = Column(String, nullable=False)
    repo = Column(String, nullable=False)

    userRoleForPipeline = query_expression()
