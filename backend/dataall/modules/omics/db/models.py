import enum

from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import query_expression, relationship

from ...db import Base, Resource, utils


class OmicsWorkflowType(enum.Enum):
    PRIVATE = "PRIVATE"
    READY2RUN = "READY2RUN"


class OmicsPipeline(Resource, Base):
    __tablename__ = "omicspipeline"
    OmicsPipelineUri = Column(String, nullable=False, primary_key=True, default=utils.uuid("OmicsPipelineUri"))
    environmentUri = Column(String, ForeignKey("environment.environmentUri", ondelete="cascade"), nullable=False)
    organizationUri = Column(String, nullable=False)
    region = Column(String, default="eu-west-1")
    AwsAccountId = Column(String, nullable=False)
    SamlGroupName = Column(String, nullable=False)
    CodeRepository = Column(String, nullable=True, default="Unknown")
    CiPipeline = Column(String, nullable=True, default="Unknown")
    CiPipelineStatus = Column(String, nullable=True, default="PENDING_CREATION")
    StepFunction = Column(String, nullable=True, default="Unknown")
    StepFunctionStatus = Column(String, nullable=True, default="PENDING_CREATION")
    OmicsWorkflow = Column(String, nullable=True, default="Unknown")
    OmicsWorkflowStatus = Column(String, nullable=True, default="PENDING_CREATION")
    S3InputBucket = Column(String, nullable=True)
    S3InputPrefix = Column(String, nullable=True)
    S3OutputBucket = Column(String, nullable=False)
    S3OutputPrefix = Column(String, nullable=False)
    AwsResources = Column(JSON, nullable=True)
    userRoleForPipeline = query_expression()
