import logging

from dataall.base.aws.sts import SessionHelper
from dataall.base.cdkproxy.cdk_cli_wrapper import CDKCliWrapperExtension, describe_stack, update_stack_output
from dataall.modules.datapipelines.cdk.datapipelines_cdk_pipeline import CDKPipelineStack
from dataall.modules.datapipelines.db.datapipelines_repositories import DatapipelinesRepository


logger = logging.getLogger('cdksass')


class DatapipelinesCDKCliWrapperExtension(CDKCliWrapperExtension):
    def __init__(self):
        pass

    def extend_deployment(self, stack, session, env):
        cdkpipeline = CDKPipelineStack(stack.targetUri)
        is_create = cdkpipeline.is_create if cdkpipeline.is_create else None
        self.pipeline = DatapipelinesRepository.get_pipeline_by_uri(session, stack.targetUri)
        path = f'{cdkpipeline.code_dir_path}/{self.pipeline.repo}/'
        app_path = './app.py'
        if not is_create:
            logger.info('Successfully Updated CDK Pipeline')
            meta = describe_stack(stack)
            stack.stackid = meta['StackId']
            stack.status = meta['StackStatus']
            update_stack_output(session, stack)
            return True, path, app_path

        aws = SessionHelper.remote_session(stack.accountid, stack.region)
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

        return False, path, app_path

    def post_deployment(self):
        CDKPipelineStack.clean_up_repo(pipeline_dir=self.pipeline.repo)
