from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import JSON

from backend.db import Base, Resource, utils


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
