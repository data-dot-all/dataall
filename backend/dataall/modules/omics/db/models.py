import enum

from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import query_expression, relationship

from ...db import Base, Resource, utils


class OmicsWorkflowType(enum.Enum):
    PRIVATE = "PRIVATE"
    READY2RUN = "READY2RUN"

## TODO: define the fields in the RDS tables
class OmicsWorkflow(Resource, Base):
    __tablename__ = "omics_workflow"
    workflowUri = Column(String, nullable=False, primary_key=True, default=utils.uuid("omicsWorkflowUri"))
    # TODO: add...

class OmicsRun(Resource, Base):
    __tablename__ = "omics_run"
    runUri = Column(String, nullable=False, primary_key=True, default=utils.uuid("omicsRunUri"))
    workflowUri = Column(String, nullable=False)
    environmentUri = Column(String, ForeignKey("environment.environmentUri", ondelete="cascade"), nullable=False)
    organizationUri = Column(String, nullable=False)
    region = Column(String, default="eu-west-1")
    AwsAccountId = Column(String, nullable=False)
    SamlGroupName = Column(String, nullable=False)
    # TODO: add fields
    userRoleForPipeline = query_expression()