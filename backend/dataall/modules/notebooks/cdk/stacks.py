""""
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

from dataall.modules.notebooks.models import SagemakerNotebook
from dataall.db.models import EnvironmentGroup

from dataall.cdkproxy.stacks.manager import stack
from dataall.db import Engine, get_engine
from dataall.db.api import Environment
from dataall.utils.cdk_nag_utils import CDKNagUtil
from dataall.utils.runtime_stacks_tagging import TagsUtil

logger = logging.getLogger(__name__)


@stack(stack='notebook')
class SagemakerNotebook(Stack):
    """
    Creation of a notebook stack.
    Having imported the notebook module, the class registers itself using @stack
    Then it will be reachable by HTTP request from GraphQL lambda
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

    def get_env_group(
        self, notebook: SagemakerNotebook
    ) -> EnvironmentGroup:
        engine = self.get_engine()
        with engine.scoped_session() as session:
            env = Environment.get_environment_group(
                session, notebook.SamlAdminGroupName, notebook.environmentUri
            )
        return env

    def __init__(self, scope, id: str, target_uri: str = None, **kwargs) -> None:
        super().__init__(scope,
                         id,
                         description="Cloud formation stack of NOTEBOOK: {}; URI: {}; DESCRIPTION: {}".format(
                             self.get_target(target_uri=target_uri).label,
                             target_uri,
                             self.get_target(target_uri=target_uri).description,
                         )[:1024],
                         **kwargs)

        # Required for dynamic stack tagging
        self.target_uri = target_uri

        notebook = self.get_target(target_uri=target_uri)

        env_group = self.get_env_group(notebook)

        notebook_key = kms.Key(
            self,
            'NotebookKmsKey',
            alias=notebook.NotebookInstanceName,
            enable_key_rotation=True,
            policy=iam.PolicyDocument(
                assign_sids=True,
                statements=[
                    iam.PolicyStatement(
                        resources=['*'],
                        effect=iam.Effect.ALLOW,
                        principals=[
                            iam.AccountPrincipal(account_id=notebook.AWSAccountId),
                            iam.Role.from_role_arn(
                                self,
                                'NotebookRole',
                                role_arn=notebook.RoleArn,
                            ),
                        ],
                        actions=['kms:*'],
                    )
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
                role_arn=env_group.environmentIAMRoleArn,
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

        TagsUtil.add_tags(self)

        CDKNagUtil.check_rules(self)
