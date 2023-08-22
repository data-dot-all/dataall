import enum

from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import query_expression, relationship

from dataall.base.db import Base
from dataall.base.db import Resource, utils


class OmicsWorkflowType(enum.Enum):
    PRIVATE = "PRIVATE"
    READY2RUN = "READY2RUN"

## TODO: define the fields in the RDS tables
class OmicsWorkflow(Resource, Base):
    __tablename__ = "omics_workflow"
    # workflowid = Column(String, nullable=False, primary_key=True, default=utils.uuid("omicsWorkflowUri"))
    arn = Column(String, nullable=False)
    id = Column(String, nullable=False, primary_key=True, default=utils.uuid("omicsWorkflowUri"))
    label = Column(String, nullable=False, default=utils.uuid("omicsWorkflowUri"))
    owner = Column(String, nullable=False, default=utils.uuid("omicsWorkflowUri"))
    name = Column(String, nullable=False)
    status = Column(String, nullable=False)
    type = Column(String, nullable=False)
    description = Column(String, nullable=True)
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