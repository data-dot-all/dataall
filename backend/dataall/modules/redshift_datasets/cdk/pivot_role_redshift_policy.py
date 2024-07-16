import os
from aws_cdk import aws_iam as iam

from dataall.base import db
from dataall.base.aws.sts import SessionHelper
from dataall.base.utils.iam_policy_utils import split_policy_with_resources_in_statements
from dataall.core.environment.cdk.pivot_role_stack import PivotRoleStatementSet
from dataall.modules.redshift_datasets.db.redshift_connection_repositories import RedshiftConnectionRepository
from dataall.modules.redshift_datasets.aws.redshift_serverless import RedshiftServerless


class RedshiftDatasetsPivotRole(PivotRoleStatementSet):
    """
    Class including all permissions needed  by the pivot role to work with Amazon Redshift.
    """

    def get_statements(self):
        base_statements = [
            iam.PolicyStatement(
                sid='RedshiftSecretsManager',
                effect=iam.Effect.ALLOW,
                actions=[
                    'secretsmanager:GetSecretValue',
                ],
                resources=[
                    f'arn:aws:secretsmanager:{self.region}:{self.account}:secret:*',
                ],
                conditions={
                    'StringEquals': {
                        'aws:ResourceTag/dataall': 'True',
                        # TODO: add in instructions that it is needed to tag the resource also with Redshift tag
                    },
                },
            ),
            iam.PolicyStatement(
                sid='RedshiftRead',
                effect=iam.Effect.ALLOW,
                actions=[
                    'redshift-data:DescribeStatement',
                    'redshift:DescribeClusters',
                    'redshift-serverless:ListNamespaces',
                    'redshift-serverless:GetWorkgroup',
                    'redshift-serverless:ListWorkgroups'
                ],
                resources=[
                    '*',
                ],
            ),
            iam.PolicyStatement(
                sid='RedshiftLakeFormationGlue',
                effect=iam.Effect.ALLOW,
                actions=[
                    'lakeformation:RegisterResource',
                    'glue:PassConnection'
                ],
                resources=[
                    f'arn:aws:lakeformation:{self.region}:{self.account}:catalog:{self.account}',
                    f'arn:aws:glue:{self.region}:{self.account}:connection/aws:redshift'
                ],
            ),
        ]
        engine = db.get_engine(envname=os.environ.get('envname', 'local'))
        with engine.scoped_session() as session:
            connections = RedshiftConnectionRepository.query_environment_redshift_connections(
                session, environment_uri=self.environmentUri
            )
            additional_statements = []
            if connections:
                cdk_look_up_role_arn = SessionHelper.get_cdk_look_up_role_arn(
                    accountid=self.account, region=self.region
                )
                # TODO: SCOPE DOWN PERMISSIONS and keep elaborating on the arns (cluster is not done)
                rs_client = RedshiftServerless(account_id=self.account, region=self.region, role=cdk_look_up_role_arn)
                cluster_arns = [conn.clusterId for conn in connections if conn.clusterId != '']
                workgroup_arns = [
                    rs_client.get_workgroup_arn(workgroup_name=conn.workgroup)
                    for conn in connections
                    if conn.workgroup != ''
                ]
                # namespaces_arns = [conn.nameSpaceId for conn in connections if conn.nameSpaceId != '']
                datashare_arns = [
                    f'arn:aws:redshift:{self.region}:{self.account}:datashare:{conn.nameSpaceId}/*'
                    for conn in connections
                    if conn.nameSpaceId != ''
                ]
                additional_statements.extend(
                    split_policy_with_resources_in_statements(
                        base_sid='RedshiftData',
                        effect=iam.Effect.ALLOW,
                        actions=[
                            'redshift-data:ListSchemas',
                            'redshift-data:ListDatabases',
                            'redshift-serverless:GetCredentials',
                            'redshift:GetClusterCredentials',
                            'redshift:GetClusterCredentialsWithIAM',
                            'redshift-data:ListTables',
                            'redshift-data:ExecuteStatement',
                        ],
                        resources=cluster_arns + workgroup_arns,
                    )
                )
                additional_statements.extend(
                    split_policy_with_resources_in_statements(
                        base_sid='RedshiftDataShare',
                        effect=iam.Effect.ALLOW,
                        actions=[
                            'redshift:AuthorizeDataShare',
                            'redshift:AssociateDataShareConsumer',
                            'redshift:DescribeDataShares',
                        ],
                        resources=datashare_arns,
                    )
                )

        return base_statements + additional_statements
