from aws_cdk import Stage, Tags, Aspects
from cdk_nag import AwsSolutionsChecks, NagSuppressions, NagPackSuppression

from .backend_stack import BackendStack
from .cdk_nag_exclusions import BACKEND_STACK_CDK_NAG_EXCLUSIONS


class BackendStage(Stage):
    def __init__(
        self,
        scope,
        id: str,
        envname='dev',
        resource_prefix='dataall',
        ecr_repository=None,
        commit_id=None,
        tooling_account_id=None,
        pipeline_bucket=None,
        vpc_id=None,
        vpc_restricted_nacls=False,
        vpc_endpoints_sg=None,
        internet_facing=True,
        custom_domain=None,
        ip_ranges=None,
        apig_vpce=None,
        prod_sizing=False,
        quicksight_enabled=False,
        enable_cw_canaries=False,
        enable_cw_rum=False,
        shared_dashboard_sessions='anonymous',
        enable_opensearch_serverless=False,
        enable_pivot_role_auto_create=False,
        codeartifact_domain_name=None,
        codeartifact_pip_repo_name=None,
        cognito_user_session_timeout_inmins=43200,
        email_notification_sender_email_id=None,
        reauth_config=None,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        backend_stack = BackendStack(
            self,
            f'backend-stack',
            envname=envname,
            resource_prefix=resource_prefix,
            tooling_account_id=tooling_account_id,
            ecr_repository=ecr_repository,
            pipeline_bucket=pipeline_bucket,
            image_tag=commit_id,
            vpc_id=vpc_id,
            vpc_restricted_nacls=vpc_restricted_nacls,
            vpc_endpoints_sg=vpc_endpoints_sg,
            internet_facing=internet_facing,
            custom_domain=custom_domain,
            ip_ranges=ip_ranges,
            apig_vpce=apig_vpce,
            prod_sizing=prod_sizing,
            quicksight_enabled=quicksight_enabled,
            enable_cw_canaries=enable_cw_canaries,
            enable_cw_rum=enable_cw_rum,
            shared_dashboard_sessions=shared_dashboard_sessions,
            enable_opensearch_serverless=enable_opensearch_serverless,
            enable_pivot_role_auto_create=enable_pivot_role_auto_create,
            codeartifact_domain_name=codeartifact_domain_name,
            codeartifact_pip_repo_name=codeartifact_pip_repo_name,
            cognito_user_session_timeout_inmins=cognito_user_session_timeout_inmins,
            email_notification_sender_email_id=email_notification_sender_email_id,
            reauth_config=reauth_config,
            **kwargs,
        )

        Tags.of(backend_stack).add('Application', f'{resource_prefix}-{envname}')

        Aspects.of(backend_stack).add(AwsSolutionsChecks(reports=True, verbose=True))

        NagSuppressions.add_stack_suppressions(
            backend_stack,
            suppressions=[
                NagPackSuppression(id=rule_suppressed['id'], reason=rule_suppressed['reason'])
                for rule_suppressed in BACKEND_STACK_CDK_NAG_EXCLUSIONS
            ],
            apply_to_nested_stacks=True,
        )
