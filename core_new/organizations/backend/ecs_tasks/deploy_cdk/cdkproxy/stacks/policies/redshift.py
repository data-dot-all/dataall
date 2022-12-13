from aws_cdk import aws_iam as iam

from .service_policy import ServicePolicy


class Redshift(ServicePolicy):
    def get_statements(self):
        return [
            iam.PolicyStatement(
                actions=[
                    'redshift:List*',
                    'redshift:ModifySavedQuery',
                    'redshift:CreateSavedQuery',
                    'redshift:FetchResults',
                    'redshift:ViewQueriesFromConsole',
                    'redshift:CancelQuery',
                    'redshift:Describe*',
                    'redshift:ExecuteQuery',
                    'redshift:DeleteSavedQueries',
                    'redshift-data:ListTables',
                    'redshift-data:ListTables',
                    'redshift-data:GetStatementResult',
                    'redshift-data:CancelStatement',
                    'redshift-data:ListSchemas',
                    'redshift-data:ExecuteStatement',
                    'redshift-data:ListStatements',
                    'redshift-data:ListDatabases',
                    'redshift-data:DescribeStatement',
                ],
                resources=['*'],
                effect=iam.Effect.ALLOW,
            ),
            iam.PolicyStatement(
                actions=[
                    'redshift:DeleteCluster',
                    'redshift:RejectDataShare',
                    'redshift:CancelResize',
                    'redshift:ModifyClusterIamRoles',
                    'redshift:PauseCluster',
                    'redshift:ResumeCluster',
                    'redshift:CreateEventSubscription',
                    'redshift:RebootCluster',
                    'redshift:CreateClusterSnapshot',
                    'redshift:DeleteClusterSnapshot',
                    'redshift:AuthorizeDataShare',
                    'redshift:CopyClusterSnapshot',
                    'redshift:CreateCluster',
                    'redshift:GetClusterCredentials',
                    'redshift:JoinGroup',
                    'redshift:ModifyCluster',
                    'redshift:AssociateDataShareConsumer',
                    'redshift:DeleteEventSubscription',
                    'redshift:DeauthorizeDataShare',
                    'redshift:ModifyEventSubscription',
                    'redshift:DisassociateDataShareConsumer',
                ],
                resources=[
                    f'arn:aws:redshift:{self.region}:{self.account}:dbgroup:{self.resource_prefix}*/*',
                    f'arn:aws:redshift:{self.region}:{self.account}:datashare:{self.resource_prefix}*/*',
                    f'arn:aws:redshift:{self.region}:{self.account}:dbuser:{self.resource_prefix}*/*',
                    f'arn:aws:redshift:{self.region}:{self.account}:snapshot:{self.resource_prefix}*/*',
                    f'arn:aws:redshift:{self.region}:{self.account}:cluster:{self.resource_prefix}*',
                    f'arn:aws:redshift:{self.region}:{self.account}:eventsubscription:{self.resource_prefix}*',
                    f'arn:aws:redshift:{self.region}:{self.account}:dbname:{self.resource_prefix}*/*',
                ],
                effect=iam.Effect.ALLOW,
            ),
        ]
