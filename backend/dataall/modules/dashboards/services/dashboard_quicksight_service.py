import os

from dataall.base.aws.parameter_store import ParameterStoreManager
from dataall.base.aws.sts import SessionHelper
from dataall.base.context import get_context
from dataall.base.db.exceptions import UnauthorizedOperation, TenantUnauthorized, AWSResourceNotFound
from dataall.base.utils import Parameter
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.permissions.services.tenant_permissions import TENANT_ALL
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService, TenantPolicyValidationService
from dataall.modules.dashboards.aws.dashboard_quicksight_client import DashboardQuicksightClient
from dataall.modules.dashboards.db.dashboard_models import Dashboard
from dataall.modules.dashboards.db.dashboard_repositories import DashboardRepository
from dataall.modules.dashboards.services.dashboard_permissions import GET_DASHBOARD, CREATE_DASHBOARD, MANAGE_DASHBOARDS


class DashboardQuicksightService:
    _PARAM_STORE = Parameter()
    _REGION = os.getenv('AWS_REGION', 'eu-west-1')

    @classmethod
    @ResourcePolicyService.has_resource_permission(GET_DASHBOARD)
    def get_quicksight_reader_url(cls, uri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            dash: Dashboard = DashboardRepository.get_dashboard_by_uri(session, uri)
            env = EnvironmentService.get_environment_by_uri(session, dash.environmentUri)
            cls._check_dashboards_enabled(session, env, GET_DASHBOARD)
            client = cls._client(env.AwsAccountId, env.region)

            if dash.SamlGroupName in context.groups:
                return client.get_reader_session(
                    dashboard_id=dash.DashboardId,
                    domain_name=DashboardQuicksightService._get_domain_url(),
                )

            else:
                shared_groups = DashboardRepository.query_all_user_groups_shareddashboard(
                    session=session, groups=context.groups, uri=uri
                )
                if not shared_groups:
                    raise UnauthorizedOperation(
                        action=GET_DASHBOARD,
                        message='Dashboard has not been shared with your Teams',
                    )

                session_type = ParameterStoreManager.get_parameter_value(
                    parameter_path=f'/dataall/{os.getenv("envname", "local")}/quicksight/sharedDashboardsSessions'
                )

                if session_type == 'reader':
                    return client.get_shared_reader_session(
                        group_name=shared_groups[0],
                        dashboard_id=dash.DashboardId,
                    )
                else:
                    return client.get_anonymous_session(dashboard_id=dash.DashboardId)

    @classmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_DASHBOARDS)
    @ResourcePolicyService.has_resource_permission(CREATE_DASHBOARD)
    def get_quicksight_designer_url(cls, uri: str):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            env = EnvironmentService.get_environment_by_uri(session, uri)
            cls._check_dashboards_enabled(session, env, CREATE_DASHBOARD)

            return cls._client(env.AwsAccountId, env.region).get_author_session()

    @staticmethod
    def get_monitoring_dashboard_id():
        DashboardQuicksightService._check_user_must_be_admin()
        current_account = SessionHelper.get_account()
        dashboard_id = ParameterStoreManager.get_parameter_value(
            AwsAccountId=current_account,
            region=DashboardQuicksightService._REGION,
            parameter_path=f'/dataall/{os.getenv("envname", "local")}/quicksightmonitoring/DashboardId',
        )

        if not dashboard_id:
            raise AWSResourceNotFound(
                action='GET_DASHBOARD_ID',
                message='Dashboard Id could not be found on AWS Parameter Store',
            )
        return dashboard_id

    @staticmethod
    def get_monitoring_vpc_connection_id():
        DashboardQuicksightService._check_user_must_be_admin()
        current_account = SessionHelper.get_account()
        vpc_connection_id = ParameterStoreManager.get_parameter_value(
            AwsAccountId=current_account,
            region=DashboardQuicksightService._REGION,
            parameter_path=f'/dataall/{os.getenv("envname", "local")}/quicksightmonitoring/VPCConnectionId',
        )

        if not vpc_connection_id:
            raise AWSResourceNotFound(
                action='GET_VPC_CONNECTION_ID',
                message='VPC Connection Id could not be found on AWS Parameter Store',
            )
        return vpc_connection_id

    @classmethod
    def create_quicksight_data_source_set(cls, vpc_connection_id):
        cls._check_user_must_be_admin()
        client = cls._client()
        client.register_user_in_group(group_name='dataall', user_role='AUTHOR')

        datasource_id = client.create_data_source_vpc(vpc_connection_id=vpc_connection_id)
        # Data sets are not created programmatically. Too much overhead for the value added.
        # However, an example API is provided: datasets = Quicksight.create_data_set_from_source(
        #   AwsAccountId=current_account, region=region, UserName='dataallTenantUser',
        #   dataSourceId=datasourceId, tablesToImport=['organization',
        #   'environment', 'dataset', 'datapipeline', 'dashboard', 'share_object']
        # )

        return datasource_id

    @classmethod
    def get_quicksight_reader_session(cls, dashboard_uri):
        cls._check_user_must_be_admin()
        client = cls._client()
        return client.get_reader_session(user_role='READER', dashboard_id=dashboard_uri)

    @staticmethod
    def _check_user_must_be_admin():
        context = get_context()
        admin = TenantPolicyValidationService.is_tenant_admin(context.groups)

        if not admin:
            raise TenantUnauthorized(
                username=context.username,
                action=TENANT_ALL,
                tenant_name=context.username,
            )

    @staticmethod
    def _get_domain_url():
        envname = os.getenv('envname', 'local')
        if envname in ['local', 'dkrcompose']:
            return 'http://localhost:8080'

        domain_name = DashboardQuicksightService._PARAM_STORE.get_parameter(
            env=envname, path='frontend/custom_domain_name'
        )

        return f'https://{domain_name}'

    @staticmethod
    def _check_dashboards_enabled(session, env, action):
        enabled = EnvironmentService.get_boolean_env_param(session, env, 'dashboardsEnabled')
        if not enabled:
            raise UnauthorizedOperation(
                action=action,
                message=f'Dashboards feature is disabled for the environment {env.label}',
            )

    @classmethod
    def _client(cls, account_id: str = None, region: str = None):
        if not account_id:
            account_id = SessionHelper.get_account()

        if not region:
            region = cls._REGION
        return DashboardQuicksightClient(get_context().username, account_id, region)
