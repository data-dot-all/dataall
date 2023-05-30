import os

from dataall.aws.handlers.parameter_store import ParameterStoreManager
from dataall.aws.handlers.quicksight import Quicksight
from dataall.aws.handlers.sts import SessionHelper
from dataall.core.context import get_context
from dataall.core.permission_checker import has_resource_permission
from dataall.db.api import Environment, TenantPolicy
from dataall.db.exceptions import UnauthorizedOperation, TenantUnauthorized, AWSResourceNotFound
from dataall.db.permissions import TENANT_ALL
from dataall.modules.dashboards import DashboardRepository, Dashboard
from dataall.modules.dashboards.services.dashboard_permissions import GET_DASHBOARD, CREATE_DASHBOARD
from dataall.utils import Parameter


class DashboardQuicksightService:
    _PARAM_STORE = Parameter()
    _REGION = os.getenv('AWS_REGION', 'eu-west-1')

    @staticmethod
    def _get_env_uri(session, uri):
        dashboard: Dashboard = DashboardRepository.get_dashboard_by_uri(session, uri)
        return dashboard.environmentUri

    @staticmethod
    @has_resource_permission(GET_DASHBOARD, parent_resource=_get_env_uri)
    def get_quicksight_reader_url(uri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            dash: Dashboard = DashboardRepository.get_dashboard_by_uri(session, uri)
            env = Environment.get_environment_by_uri(session, dash.environmentUri)
            if not env.dashboardsEnabled:
                raise UnauthorizedOperation(
                    action=GET_DASHBOARD,
                    message=f'Dashboards feature is disabled for the environment {env.label}',
                )

            if dash.SamlGroupName in context.groups:
                url = Quicksight.get_reader_session(
                    AwsAccountId=env.AwsAccountId,
                    region=env.region,
                    UserName=context.username,
                    DashboardId=dash.DashboardId,
                    domain_name=DashboardQuicksightService._get_domain_url(),
                )

            else:
                shared_groups = DashboardRepository.query_all_user_groups_shareddashboard(
                    session=session,
                    groups=context.groups,
                    uri=uri
                )
                if not shared_groups:
                    raise UnauthorizedOperation(
                        action=GET_DASHBOARD,
                        message='Dashboard has not been shared with your Teams',
                    )

                session_type = ParameterStoreManager.get_parameter_value(
                    parameter_path=f"/dataall/{os.getenv('envname', 'local')}/quicksight/sharedDashboardsSessions"
                )

                if session_type == 'reader':
                    url = Quicksight.get_shared_reader_session(
                        AwsAccountId=env.AwsAccountId,
                        region=env.region,
                        UserName=context.username,
                        GroupName=shared_groups[0],
                        DashboardId=dash.DashboardId,
                    )
                else:
                    url = Quicksight.get_anonymous_session(
                        AwsAccountId=env.AwsAccountId,
                        region=env.region,
                        UserName=context.username,
                        DashboardId=dash.DashboardId,
                    )
        return url

    @staticmethod
    @has_resource_permission(CREATE_DASHBOARD)
    def get_quicksight_designer_url(uri: str):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            env = Environment.get_environment_by_uri(session, uri)
            if not env.dashboardsEnabled:
                raise UnauthorizedOperation(
                    action=CREATE_DASHBOARD,
                    message=f'Dashboards feature is disabled for the environment {env.label}',
                )

            url = Quicksight.get_author_session(
                AwsAccountId=env.AwsAccountId,
                region=env.region,
                UserName=context.username,
                UserRole='AUTHOR',
            )

        return url

    @staticmethod
    def get_monitoring_dashboard_id():
        current_account = SessionHelper.get_account()
        dashboard_id = ParameterStoreManager.get_parameter_value(
            AwsAccountId=current_account,
            region=DashboardQuicksightService._REGION,
            parameter_path=f'/dataall/{os.getenv("envname", "local")}/quicksightmonitoring/DashboardId'
        )

        if not dashboard_id:
            raise AWSResourceNotFound(
                action='GET_DASHBOARD_ID',
                message='Dashboard Id could not be found on AWS Parameter Store',
            )
        return dashboard_id

    @staticmethod
    def get_monitoring_vpc_connection_id():
        current_account = SessionHelper.get_account()
        vpc_connection_id = ParameterStoreManager.get_parameter_value(
            AwsAccountId=current_account,
            region=DashboardQuicksightService._REGION,
            parameter_path=f'/dataall/{os.getenv("envname", "local")}/quicksightmonitoring/VPCConnectionId'
        )

        if not vpc_connection_id:
            raise AWSResourceNotFound(
                action='GET_VPC_CONNECTION_ID',
                message='VPC Connection Id could not be found on AWS Parameter Store',
            )
        return vpc_connection_id

    @staticmethod
    def create_quicksight_data_source_set(vpc_connection_id):
        context = get_context()
        current_account = SessionHelper.get_account()
        Quicksight.register_user_in_group(
            AwsAccountId=current_account,
            UserName=context.username,
            GroupName='dataall',
            UserRole='AUTHOR')

        datasource_id = Quicksight.create_data_source_vpc(
            AwsAccountId=current_account,
            region=DashboardQuicksightService._REGION,
            UserName=context.username,
            vpcConnectionId=vpc_connection_id
        )
        # Data sets are not created programmatically. Too much overhead for the value added.
        # However, an example API is provided: datasets = Quicksight.create_data_set_from_source(
        #   AwsAccountId=current_account, region=region, UserName='dataallTenantUser',
        #   dataSourceId=datasourceId, tablesToImport=['organization',
        #   'environment', 'dataset', 'datapipeline', 'dashboard', 'share_object']
        # )

        return datasource_id

    @staticmethod
    def get_quicksight_author_session(aws_account):
        DashboardQuicksightService._check_user_must_be_admin()

        return Quicksight.get_author_session(
            AwsAccountId=aws_account,
            region=DashboardQuicksightService._REGION,
            UserName=get_context().username,
            UserRole='AUTHOR',
        )

    @staticmethod
    def get_quicksight_reader_session(dashboard_uri):
        DashboardQuicksightService._check_user_must_be_admin()
        current_account = SessionHelper.get_account()

        return Quicksight.get_reader_session(
            AwsAccountId=current_account,
            region=DashboardQuicksightService._REGION,
            UserName=get_context().username,
            UserRole='READER',
            DashboardId=dashboard_uri
        )

    @staticmethod
    def _check_user_must_be_admin():
        context = get_context()
        admin = TenantPolicy.is_tenant_admin(context.groups)

        if not admin:
            raise TenantUnauthorized(
                username=context.username,
                action=TENANT_ALL,
                tenant_name=context.username,
            )

    @staticmethod
    def _get_domain_url():
        envname = os.getenv("envname", "local")
        if envname in ["local", "dkrcompose"]:
            return "http://localhost:8080"

        domain_name = DashboardQuicksightService._PARAM_STORE.get_parameter(
            env=envname,
            path="frontend/custom_domain_name"
        )

        return f"https://{domain_name}"

