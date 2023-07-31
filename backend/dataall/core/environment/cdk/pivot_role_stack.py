from typing import List
from constructs import Construct
from aws_cdk import Duration, aws_iam as iam, NestedStack


class PivotRoleStatementSet(object):
    def __init__(
            self,
            env_resource_prefix,
            role_name,
            account,
            region
    ):
        self.env_resource_prefix = env_resource_prefix
        self.role_name = role_name
        self.account = account
        self.region = region

    def generate_policies(self) -> List[iam.ManagedPolicy]:
        """
        Creates a list of aws_iam.Policy based on declared subclasses of Policy object
        """
        policies = []
        statements = []
        services = PivotRoleStatementSet.__subclasses__()

        for service in services:
            statements.extend(service.get_statements(self))

        statements_chunks: list = [
            statements[i: i + 10] for i in range(0, len(statements), 10)
        ]

        for index, chunk in enumerate(statements_chunks):
            policies.append(
                iam.ManagedPolicy(
                    self,
                    f'PivotRolePolicy-{index+1}',
                    managed_policy_name=f'{self.env_resource_prefix}-pivotrole-cdk-policy-{index+1}',
                    statements=chunk,
                )
            )
        return policies

    def get_statements(self) -> List[iam.PolicyStatement]:
        """
        This method returns the list of IAM policy statements needed to be added to the pivot role policies
        :return: list
        """
        raise NotImplementedError(
            'PivotRoleStatementSet subclasses need to implement the get_statements class method'
        )

class PivotRole(NestedStack):
    def __init__(self, scope: Construct, construct_id: str, config, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.env_resource_prefix = config['resourcePrefix']
        self.role_name = config['roleName']

        # Create Pivot IAM Role
        self.pivot_role = self.create_pivot_role(
            principal_id=config['accountId'],
            external_id=config['externalId'],
        )

        # Data.All IAM Lake Formation service role creation
        self.lf_service_role = iam.CfnServiceLinkedRole(
            self, 'LakeFormationSLR', aws_service_name='lakeformation.amazonaws.com'
        )

    def create_pivot_role(self, principal_id: str, external_id: str) -> iam.Role:
        """
        Creates an IAM Role that will enable data.all to interact with this Data Account

        :param str name: Role name
        :param str principal_id: AWS Account ID of central data.all
        :param str external_id: External ID provided by data.all
        :param str env_resource_prefix: Environment Resource Prefix provided by data.all
        :returns: Created IAM Role
        :rtype: iam.Role
        """
        managed_policies = PivotRoleStatementSet(
            env_resource_prefix=self.env_resource_prefix,
            role_name=self.role_name,
            account=self.account,
            region=self.region
        ).generate_policies()
        role = iam.Role(
            self,
            'DataAllPivotRole-cdk',
            role_name=self.role_name,
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal('lakeformation.amazonaws.com'),
                iam.ServicePrincipal('glue.amazonaws.com'),
                iam.ServicePrincipal('lambda.amazonaws.com'),
            ),
            path='/',
            max_session_duration=Duration.hours(12),
            managed_policies=managed_policies
        )

        role.assume_role_policy.add_statements(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                principals=[iam.AccountPrincipal(account_id=principal_id)],
                actions=['sts:AssumeRole'],
                conditions={
                    'StringEquals': {'sts:ExternalId': external_id},
                    'StringLike': {"aws:PrincipalArn": [
                        f"arn:aws:iam::{principal_id}:role/*graphql-role",
                        f"arn:aws:iam::{principal_id}:role/*awsworker-role",
                        f"arn:aws:iam::{principal_id}:role/*ecs-tasks-role"
                    ]}
                },
            )
        )

        return role