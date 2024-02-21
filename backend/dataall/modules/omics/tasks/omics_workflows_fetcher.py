import logging
import os
import sys

from dataall.core.environment.db.environment_models import Environment
from dataall.base.db import get_engine
from dataall.modules.omics.aws.omics_client import OmicsClient
from dataall.modules.omics.db.omics_models import OmicsWorkflow
from dataall.modules.omics.services.omics_enums import OmicsWorkflowType
from dataall.modules.omics.db.omics_repository import OmicsRepository


root = logging.getLogger()
root.setLevel(logging.INFO)
if not root.hasHandlers():
    root.addHandler(logging.StreamHandler(sys.stdout))
log = logging.getLogger(__name__)


def fetch_omics_workflows(engine):
    """List Omics workflows."""
    log.info('Starting omics workflows fetcher')
    with engine.scoped_session() as session:
        environments = session.query(Environment)
        is_first_time = True
        for env in environments:
            ready_workflows = OmicsClient.list_workflows(awsAccountId=env.AwsAccountId, region=env.region, type=OmicsWorkflowType.READY2RUN.value)
            private_workflows = OmicsClient.list_workflows(awsAccountId=env.AwsAccountId, region=env.region, type=OmicsWorkflowType.PRIVATE.value)
            workflows = ready_workflows + private_workflows
            log.info(f"Found workflows {str(workflows)} in environment {env.environmentUri}")
            for workflow in workflows:
                log.info(f"Processing workflow name={workflow['name']}, id={workflow['id']}...")
                existing_workflow = OmicsRepository(session).get_workflow(workflow['id'])
                if existing_workflow is not None:
                    log.info(f"Workflow name={workflow['name']}, id={workflow['id']} has already been registered in database. Skipping...")
                elif is_first_time or workflow['type'] == OmicsWorkflowType.PRIVATE.value:
                    log.info(f"Workflow name={workflow['name']} , id={workflow['id']} in environment {env.environmentUri} is new. Registering...")
                    omicsWorkflow = OmicsWorkflow(
                        id=workflow['id'],
                        name=workflow['name'],
                        arn=workflow['arn'],
                        status=workflow['status'],
                        type=workflow['type'],
                        environmentUri=env.environmentUri,
                    )
                    OmicsRepository(session).save_omics_workflow(omicsWorkflow)
            is_first_time = False
    return True


if __name__ == '__main__':
    ENVNAME = os.environ.get('envname', 'local')
    ENGINE = get_engine(envname=ENVNAME)
    fetch_omics_workflows(engine=ENGINE)
