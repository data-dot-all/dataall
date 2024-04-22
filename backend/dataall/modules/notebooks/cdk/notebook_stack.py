""" "
Creates a CloudFormation stack for SageMaker notebooks using cdk
"""

import logging
import os

from aws_cdk import (
    aws_sagemaker as sagemaker,
    aws_ec2 as ec2,
    aws_kms as kms,
    aws_iam as iam,
    Stack,
    CfnOutput,
)

from dataall.base.aws.sts import SessionHelper
from dataall.base.cdkproxy.stacks.manager import stack
from dataall.core.environment.db.environment_models import EnvironmentGroup
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.stacks.services.runtime_stacks_tagging import TagsUtil
from dataall.base.db import Engine, get_engine
from dataall.modules.notebooks.db.notebook_models import SagemakerNotebook
from dataall.base.utils.cdk_nag_utils import CDKNagUtil

logger = logging.getLogger(__name__)


@stack(stack='notebook')
class NotebookStack(Stack):
    """
    Creation of a notebook stack.
    Having imported the notebook module, the class registers itself using @stack
    Then it will be reachable by HTTP request / using SQS from GraphQL lambda
    """

    module_name = __file__

    def get_engine(self) -> Engine:
        envname = os.environ.get('envname', 'local')
        engine = get_engine(envname=envname)
        return engine

    def get_target(self, target_uri) -> SagemakerNotebook:
        engine = self.get_engine()
        with engine.scoped_session() as session:
            notebook = session.query(SagemakerNotebook).get(target_uri)
        return notebook

    def get_env_group(self, notebook: SagemakerNotebook) -> EnvironmentGroup:
        engine = self.get_engine()
        with engine.scoped_session() as session:
            env_group = EnvironmentService.get_environment_group(
                session, notebook.SamlAdminGroupName, notebook.environmentUri
            )
        return env_group

    def __init__(self, scope, id: str, target_uri: str = None, **kwargs) -> None:
        super().__init__(
            scope,
            id,
            description='Cloud formation stack of NOTEBOOK: {}; URI: {}; DESCRIPTION: {}'.format(
                self.get_target(target_uri=target_uri).label,
                target_uri,
                self.get_target(target_uri=target_uri).description,
            )[:1024],
            **kwargs,
        )

        # Required for dynamic stack tagging
        self.target_uri = target_uri

        notebook: SagemakerNotebook = self.get_target(target_uri=target_uri)

        env_group = self.get_env_group(notebook)

        cdk_exec_role = SessionHelper.get_cdk_exec_role_arn(notebook.AWSAccountId, notebook.region)

        notebook_key = kms.Key(
            self,
            'NotebookKmsKey',
            alias=notebook.NotebookInstanceName,
            enable_key_rotation=True,
            admins=[
                iam.ArnPrincipal(cdk_exec_role),
            ],
            policy=iam.PolicyDocument(
                assign_sids=True,
                statements=[
                    iam.PolicyStatement(
                        resources=['*'],
                        effect=iam.Effect.ALLOW,
                        principals=[iam.ArnPrincipal(notebook.RoleArn)],
                        actions=[
                            'kms:Encrypt',
                            'kms:Decrypt',
                            'kms:ReEncrypt*',
                            'kms:GenerateDataKey*',
                            'kms:DescribeKey',
                        ],
                        conditions={'StringEquals': {'kms:ViaService': f'sagemaker.{notebook.region}.amazonaws.com'}},
                    ),
                    iam.PolicyStatement(
                        resources=['*'],
                        effect=iam.Effect.ALLOW,
                        principals=[iam.ArnPrincipal(notebook.RoleArn)],
                        actions=[
                            'kms:DescribeKey',
                            'kms:List*',
                            'kms:GetKeyPolicy',
                        ],
                    ),
                ],
            ),
        )

        if not (notebook.VpcId and notebook.SubnetId):
            sagemaker.CfnNotebookInstance(
                self,
                f'Notebook{target_uri}',
                instance_type=notebook.InstanceType,
                role_arn=notebook.RoleArn,
                direct_internet_access='Enabled',
                notebook_instance_name=notebook.NotebookInstanceName,
                kms_key_id=notebook_key.key_id,
            )
        else:
            vpc = ec2.Vpc.from_lookup(self, 'NotebookVPC', vpc_id=notebook.VpcId)
            security_group = ec2.SecurityGroup(
                self,
                f'sgNotebook{target_uri}',
                vpc=vpc,
                allow_all_outbound=True,
                security_group_name=notebook.NotebookInstanceName,
            )
            security_group.connections.allow_from(
                ec2.Peer.ipv4(vpc.vpc_cidr_block),
                ec2.Port.tcp(443),
                'Allow inbound HTTPS',
            )

            sagemaker.CfnNotebookInstance(
                self,
                f'Notebook{target_uri}',
                instance_type=notebook.InstanceType,
                role_arn=notebook.RoleArn,
                direct_internet_access='Disabled',
                subnet_id=notebook.SubnetId,
                security_group_ids=[security_group.security_group_id],
                notebook_instance_name=notebook.NotebookInstanceName,
                kms_key_id=notebook_key.key_id,
                volume_size_in_gb=notebook.VolumeSizeInGB,
            )

        CfnOutput(
            self,
            'NotebookInstanceName',
            export_name=f'{notebook.notebookUri}-NotebookInstanceName',
            value=notebook.NotebookInstanceName,
        )

        TagsUtil.add_tags(stack=self, model=SagemakerNotebook, target_type='notebook')

        CDKNagUtil.check_rules(self)
