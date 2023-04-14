from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import JSON
from dataall.db import Base, Resource, utils


class DatasetTableColumn(Resource, Base):
    __tablename__ = 'dataset_table_column'
    datasetUri = Column(String, nullable=False)
    tableUri = Column(String, nullable=False)
    columnUri = Column(String, primary_key=True, default=utils.uuid('col'))
    AWSAccountId = Column(String, nullable=False)
    region = Column(String, nullable=False)
    GlueDatabaseName = Column(String, nullable=False)
    GlueTableName = Column(String, nullable=False)
    region = Column(String, default='eu-west-1')
    typeName = Column(String, nullable=False)
    columnType = Column(
        String, default='column'
    )  # can be either "column" or "partition"

    def uri(self):
        return self.columnUri


class DatasetProfilingRun(Resource, Base):
    __tablename__ = 'dataset_profiling_run'
    profilingRunUri = Column(
        String, primary_key=True, default=utils.uuid('profilingrun')
    )
    datasetUri = Column(String, nullable=False)
    GlueJobName = Column(String)
    GlueJobRunId = Column(String)
    GlueTriggerSchedule = Column(String)
    GlueTriggerName = Column(String)
    GlueTableName = Column(String)
    AwsAccountId = Column(String)
    results = Column(JSON, default={})
    status = Column(String, default='Created')
