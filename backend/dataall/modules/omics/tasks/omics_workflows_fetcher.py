import logging
import os
import sys
from operator import and_

from dataall.base.aws.sts import SessionHelper
from dataall.core.environment.db.environment_models import Environment, EnvironmentGroup
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.base.db import get_engine
from dataall.modules.omics.aws.omics_client import OmicsClient
from dataall.modules.omics.db.models import OmicsWorkflow, OmicsWorkflowType
from dataall.modules.omics.db.omics_repository import OmicsRepository


root = logging.getLogger()
root.setLevel(logging.INFO)
if not root.hasHandlers():
    root.addHandler(logging.StreamHandler(sys.stdout))
log = logging.getLogger(__name__)


def fetch_omics_workflows(engine):
    """List Omics workflows."""
    with engine.scoped_session() as session:
        environments = session.query(Environment)
        is_first_time = True
        for env in environments:
            omicsClient = OmicsClient(awsAccountId=env.AwsAccountId, region=env.region)
            workflows = omicsClient.list_workflows()
            for workflow in workflows:
                if is_first_time or workflow['type'] == OmicsWorkflowType.PRIVATE.value:
                    omicsWorkflow = OmicsWorkflow(
                        id=workflow['id'],
                        name=workflow['name'],
                        arn=workflow['arn'],
                        status=workflow['status'],
                        type=workflow['type'],
                        environmentUri=env.environmentUri,
                        awsAccount=env.AwsAccountId
                    )
                    OmicsRepository(session).save_omics_workflow(omicsWorkflow)
            is_first_time = False
    return True



if __name__ == '__main__':
    ENVNAME = os.environ.get('envname', 'local')
    ENGINE = get_engine(envname=ENVNAME)
    fetch_omics_workflows(engine=ENGINE)
