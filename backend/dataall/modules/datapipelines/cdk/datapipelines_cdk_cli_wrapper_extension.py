import logging

from dataall.aws.handlers.sts import SessionHelper
from dataall.cdkproxy.cdk_cli_wrapper import CDKCliWrapperExtension, \
    _CDK_CLI_WRAPPER_EXTENSIONS, describe_stack, update_stack_output
from dataall.modules.datapipelines.cdk.datapipelines_cdk_pipeline import CDKPipelineStack
from dataall.modules.datapipelines.db.repositories import DatapipelinesRepository


logger = logging.getLogger('cdksass')


class DatapipelinesCDKCliWrapperExtension(CDKCliWrapperExtension):
    def __init__(self):
        pass

    def extend_deployment(self, stack, session, env):
        cdkpipeline = CDKPipelineStack(stack.targetUri)
        venv_name = cdkpipeline.venv_name if cdkpipeline.venv_name else None
        self.pipeline = DatapipelinesRepository.get_pipeline_by_uri(session, stack.targetUri)
        path = f'./cdkpipeline/{self.pipeline.repo}/'
        if not venv_name:
            logger.info('Successfully Updated CDK Pipeline')
            meta = describe_stack(stack)
            stack.stackid = meta['StackId']
            stack.status = meta['StackStatus']
            update_stack_output(session, stack)
            return True, path
        
        aws = SessionHelper.remote_session(stack.accountid)
        creds = aws.get_credentials()
        env.update(
            {
                'CDK_DEFAULT_REGION': stack.region,
                'AWS_REGION': stack.region,
                'AWS_DEFAULT_REGION': stack.region,
                'CDK_DEFAULT_ACCOUNT': stack.accountid,
                'AWS_ACCESS_KEY_ID': creds.access_key,
                'AWS_SECRET_ACCESS_KEY': creds.secret_key,
                'AWS_SESSION_TOKEN': creds.token,
            }
        )

        return False, path
    
    def cleanup(self):
        CDKPipelineStack.clean_up_repo(path=f'./{self.pipeline.repo}')
