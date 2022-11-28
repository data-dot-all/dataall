from sqlalchemy import Column, String
from sqlalchemy.orm import query_expression

from .. import Base
from .. import Resource, utils


class DatasetTableProfilingJob(Resource, Base):
    __tablename__ = 'dataset_table_profiling_job'
    tableUri = Column(String, nullable=False)
    jobUri = Column(String, primary_key=True, default=utils.uuid('profilingjob'))
    AWSAccountId = Column(String, nullable=False)
    RunCommandId = Column(String, nullable=True)
    GlueDatabaseName = Column(String, nullable=False)
    GlueTableName = Column(String, nullable=False)
    region = Column(String, default='eu-west-1')
    status = Column(String, default='')
    userRoleForJob = query_expression()
