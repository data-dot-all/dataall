from sqlalchemy import Boolean, Column, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import query_expression
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


class DatasetStorageLocation(Resource, Base):
    __tablename__ = 'dataset_storage_location'
    datasetUri = Column(String, nullable=False)
    locationUri = Column(String, primary_key=True, default=utils.uuid('location'))
    AWSAccountId = Column(String, nullable=False)
    S3BucketName = Column(String, nullable=False)
    S3Prefix = Column(String, nullable=False)
    S3AccessPoint = Column(String, nullable=True)
    region = Column(String, default='eu-west-1')
    locationCreated = Column(Boolean, default=False)
    userRoleForStorageLocation = query_expression()
    projectPermission = query_expression()
    environmentEndPoint = query_expression()

    def uri(self):
        return self.locationUri
