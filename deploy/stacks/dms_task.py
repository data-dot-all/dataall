from aws_cdk import Stack, aws_dms as dms, aws_iam as iam
from constructs import Construct
from .pyNestedStack import pyNestedClass


class DMSTaskStack(pyNestedClass):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        secret_id_aurora_v1: str,
        secret_id_aurora_v2: str,
        database_name: str,
        vpc_security_group: str,
        replication_subnet_group_identifier: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        replication_role = iam.Role(
            self,
            'DMSReplicationRole',
            role_name='dataall-dms-replication-role',
            assumed_by=iam.ServicePrincipal('dms.amazonaws.com'),
        )
        replication_role.add_to_policy(
            iam.PolicyStatement(
                actions=['secretsmanager:DescribeSecret', 'secretsmanager:GetSecretValue'],
                effect=iam.Effect.ALLOW,
                resources=[secret_id_aurora_v1, secret_id_aurora_v2],
            )
        )

        cfn_replication_instance = dms.CfnReplicationInstance(
            self,
            'MyCfnReplicationInstance',
            replication_instance_class='dms.c4.large',
            vpc_security_group_ids=[vpc_security_group],
            replication_subnet_group_identifier=replication_subnet_group_identifier,
            replication_instance_identifier='test1',
        )
        cfn_endpoint_source = dms.CfnEndpoint(
            self,
            'MyCfnEndpoint',
            endpoint_type='source',
            engine_name='aurora-postgresql',
            database_name=database_name,
            postgre_sql_settings=dms.CfnEndpoint.PostgreSqlSettingsProperty(
                secrets_manager_access_role_arn=replication_role.role_arn,
                secrets_manager_secret_id=secret_id_aurora_v1,
            ),
        )

        cfn_endpoint_target = dms.CfnEndpoint(
            self,
            'MyCfnEndpointTarget',
            endpoint_type='target',
            engine_name='aurora-postgresql',
            database_name=database_name,
            postgre_sql_settings=dms.CfnEndpoint.PostgreSqlSettingsProperty(
                secrets_manager_access_role_arn=replication_role.role_arn,
                secrets_manager_secret_id=secret_id_aurora_v2,
            ),
        )

        cfn_replication_task = dms.CfnReplicationTask(
            self,
            'MyCfnReplicationTask',
            migration_type='full-load',
            replication_instance_arn=cfn_replication_instance.ref,
            source_endpoint_arn=cfn_endpoint_source.ref,
            table_mappings='{ "rules": [ { "rule-type": "selection", "rule-id": "1", "rule-name": "1", "object-locator": { "schema-name": "%", "table-name": "%" }, "rule-action": "include" } ] }',
            target_endpoint_arn=cfn_endpoint_target.ref,
        )
