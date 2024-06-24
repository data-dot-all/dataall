from dataall.modules.s3_datasets_shares.services.managed_share_policy_service import (
    SharePolicyService,
    IAM_S3_ACCESS_POINTS_STATEMENT_SID,
    IAM_S3_BUCKETS_STATEMENT_SID,
)
from migrations.dataall_migrations.base_migration import BaseDataAllMigration
from dataall.base.aws.iam import IAM
from alembic import op
from sqlalchemy import orm
from dataall.core.environment.db.environment_repositories import EnvironmentRepository
import json


class RemoveWildCard(BaseDataAllMigration):
    key = '51132fed-c36d-470c-9946-5164581856cb'
    name = 'Remove Wildcard from Sharing Policy'
    description = 'Remove Wildcard from Sharing Policy'

    previous_migration = '0'

    @staticmethod
    def get_session():
        bind = op.get_bind()
        session = orm.Session(bind=bind)
        return session

    @classmethod
    def up(cls):
        session = cls.get_session()
        all_envs = EnvironmentRepository.query_all_active_environments(session)
        for env in all_envs:
            cons_roles = EnvironmentRepository.query_all_environment_consumption_roles(session, env.environmentUri)
            for role in cons_roles:
                share_policy_service = SharePolicyService(
                    environmentUri=env.environmentUri,
                    account=env.AwsAccountId,
                    region=env.region,
                    role_name=role.IAMRoleName,
                    resource_prefix=env.resourcePrefix,
                )
                share_resource_policy_name = share_policy_service.generate_policy_name()
                version_id, policy_document = IAM.get_managed_policy_default_version(
                    env.AwsAccountId, env.region, policy_name=share_resource_policy_name
                )
                if policy_document is not None:
                    statements = policy_document.get('Statement', [])
                    for statement in statements:
                        if statement['Sid'] in [IAM_S3_BUCKETS_STATEMENT_SID, IAM_S3_ACCESS_POINTS_STATEMENT_SID]:
                            actions = set(statement['Actions'])
                            if 's3:*' in actions:
                                actions.remove('s3:*')
                                actions.add('s3:List*')
                                actions.add('s3:Describe*')
                                actions.add('s3:GetObject')
                            statement['Actions'] = list(actions)
                    policy_document['Statement'] = statements
                    IAM.update_managed_policy_default_version(
                        env.AwsAccountId,
                        env.region,
                        share_resource_policy_name,
                        version_id,
                        json.dumps(policy_document),
                    )
