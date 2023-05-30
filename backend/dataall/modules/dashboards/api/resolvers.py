import os
from dataall import db
from dataall.api.constants import DashboardRole
from dataall.api.context import Context
from dataall.aws.handlers.quicksight import Quicksight
from dataall.aws.handlers.parameter_store import ParameterStoreManager
from dataall.aws.handlers.sts import SessionHelper
from dataall.db import models
from dataall.db.api import ResourcePolicy, Glossary, Vote, TenantPolicy
from dataall.db.exceptions import RequiredParameter, AWSResourceNotFound, TenantUnauthorized
from dataall.modules.dashboards.db.dashboard_repository import DashboardRepository
from dataall.modules.dashboards.db.models import Dashboard
from dataall.modules.dashboards.services.dashboard_permissions import GET_DASHBOARD, CREATE_DASHBOARD
from dataall.modules.dashboards.services.dashboard_service import DashboardService
from dataall.modules.dashboards.services.dashboard_share_service import DashboardShareService
from dataall.utils import Parameter
from dataall.modules.dashboards.indexers.dashboard_indexer import DashboardIndexer

param_store = Parameter()
ENVNAME = os.getenv("envname", "local")
DOMAIN_NAME = param_store.get_parameter(env=ENVNAME, path="frontend/custom_domain_name") if ENVNAME not in ["local", "dkrcompose"] else None
DOMAIN_URL = f"https://{DOMAIN_NAME}" if DOMAIN_NAME else "http://localhost:8080"


def get_quicksight_reader_url(context, source, dashboardUri: str = None):
    with context.engine.scoped_session() as session:
        dash: Dashboard = session.query(Dashboard).get(dashboardUri)
        env: models.Environment = session.query(models.Environment).get(
            dash.environmentUri
        )
        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=dash.dashboardUri,
            permission_name=GET_DASHBOARD,
        )
        if not env.dashboardsEnabled:
            raise db.exceptions.UnauthorizedOperation(
                action=GET_DASHBOARD,
                message=f'Dashboards feature is disabled for the environment {env.label}',
            )
        if dash.SamlGroupName in context.groups:
            url = Quicksight.get_reader_session(
                AwsAccountId=env.AwsAccountId,
                region=env.region,
                UserName=context.username,
                DashboardId=dash.DashboardId,
                domain_name=DOMAIN_URL,
            )
        else:
            shared_groups = DashboardRepository.query_all_user_groups_shareddashboard(
                session=session,
                groups=context.groups,
                uri=dashboardUri
            )
            if not shared_groups:
                raise db.exceptions.UnauthorizedOperation(
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


def get_quicksight_designer_url(
    context, source, environmentUri: str = None, dashboardUri: str = None
):
    with context.engine.scoped_session() as session:
        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=environmentUri,
            permission_name=CREATE_DASHBOARD,
        )
        env: models.Environment = session.query(models.Environment).get(environmentUri)
        if not env.dashboardsEnabled:
            raise db.exceptions.UnauthorizedOperation(
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


def import_dashboard(context: Context, source, input: dict = None):
    if not input:
        raise RequiredParameter(input)
    if not input.get('environmentUri'):
        raise RequiredParameter('environmentUri')
    if not input.get('SamlGroupName'):
        raise RequiredParameter('group')
    if not input.get('dashboardId'):
        raise RequiredParameter('dashboardId')
    if not input.get('label'):
        raise RequiredParameter('label')

    return DashboardService.import_dashboard(uri=input['environmentUri'], data=input)


def update_dashboard(context, source, input: dict = None):
    return DashboardService.update_dashboard(uri=input['dashboardUri'], data=input)

def list_dashboards(context: Context, source, filter: dict = None):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return DashboardRepository.paginated_user_dashboards(
            session=session,
            username=context.username,
            groups=context.groups,
            data=filter,
        )


def get_dashboard(context: Context, source, dashboardUri: str = None):
    return DashboardService.get_dashboard(uri=dashboardUri)


def resolve_user_role(context: Context, source: Dashboard):
    if context.username and source.owner == context.username:
        return DashboardRole.Creator.value
    elif context.groups and source.SamlGroupName in context.groups:
        return DashboardRole.Admin.value
    return DashboardRole.Shared.value


def get_dashboard_organization(context: Context, source: Dashboard, **kwargs):
    with context.engine.scoped_session() as session:
        org = session.query(models.Organization).get(source.organizationUri)
    return org


def request_dashboard_share(
    context: Context,
    source: Dashboard,
    principalId: str = None,
    dashboardUri: str = None,
):
    return DashboardShareService.request_dashboard_share(uri=dashboardUri, principal_id=principalId)


def approve_dashboard_share(context: Context, source: Dashboard, shareUri: str = None):
    return DashboardShareService.approve_dashboard_share(uri=shareUri)


def reject_dashboard_share(context: Context,source: Dashboard, shareUri: str = None):
    return DashboardShareService.reject_dashboard_share(uri=shareUri)


def list_dashboard_shares(
    context: Context,
    source: Dashboard,
    dashboardUri: str = None,
    filter: dict = None,
):
    if not filter:
        filter = {}
    return DashboardShareService.list_dashboard_shares(uri=dashboardUri, data=filter)


def share_dashboard(
    context: Context,
    source: Dashboard,
    principalId: str = None,
    dashboardUri: str = None,
):
    return DashboardShareService.share_dashboard(uri=dashboardUri, principal_id=principalId)


def delete_dashboard(context: Context, source, dashboardUri: str = None):
    return DashboardService.delete_dashboard(uri=dashboardUri)


def resolve_glossary_terms(context: Context, source: Dashboard, **kwargs):
    with context.engine.scoped_session() as session:
        return Glossary.get_glossary_terms_links(
            session, source.dashboardUri, 'Dashboard'
        )


def resolve_upvotes(context: Context, source: Dashboard, **kwargs):
    with context.engine.scoped_session() as session:
        return Vote.count_upvotes(
            session, None, None, source.dashboardUri, data={'targetType': 'dashboard'}
        )


def get_monitoring_dashboard_id(context, source):
    current_account = SessionHelper.get_account()
    region = os.getenv('AWS_REGION', 'eu-west-1')
    dashboard_id = ParameterStoreManager.get_parameter_value(
        AwsAccountId=current_account,
        region=region,
        parameter_path=f'/dataall/{os.getenv("envname", "local")}/quicksightmonitoring/DashboardId'
    )

    if not dashboard_id:
        raise AWSResourceNotFound(
            action='GET_DASHBOARD_ID',
            message='Dashboard Id could not be found on AWS Parameter Store',
        )
    return dashboard_id


def get_monitoring_vpc_connection_id(context, source):
    current_account = SessionHelper.get_account()
    region = os.getenv('AWS_REGION', 'eu-west-1')
    vpc_connection_id = ParameterStoreManager.get_parameter_value(
        AwsAccountId=current_account,
        region=region,
        parameter_path=f'/dataall/{os.getenv("envname", "local")}/quicksightmonitoring/VPCConnectionId'
    )

    if not vpc_connection_id:
        raise AWSResourceNotFound(
            action='GET_VPC_CONNECTION_ID',
            message='VPC Connection Id could not be found on AWS Parameter Store',
        )
    return vpc_connection_id


def create_quicksight_data_source_set(context, source, vpcConnectionId: str = None):
    current_account = SessionHelper.get_account()
    region = os.getenv('AWS_REGION', 'eu-west-1')
    user = Quicksight.register_user_in_group(
        AwsAccountId=current_account,
        UserName=context.username,
        GroupName='dataall',
        UserRole='AUTHOR')

    datasourceId = Quicksight.create_data_source_vpc(AwsAccountId=current_account, region=region, UserName=context.username, vpcConnectionId=vpcConnectionId)
    # Data sets are not created programmatically. Too much overhead for the value added. However, an example API is provided:
    # datasets = Quicksight.create_data_set_from_source(AwsAccountId=current_account, region=region, UserName='dataallTenantUser', dataSourceId=datasourceId, tablesToImport=['organization', 'environment', 'dataset', 'datapipeline', 'dashboard', 'share_object'])

    return datasourceId


def get_quicksight_author_session(context, source, awsAccount: str = None):
    with context.engine.scoped_session() as session:
        admin = TenantPolicy.is_tenant_admin(context.groups)

        if not admin:
            raise TenantUnauthorized(
                username=context.username,
                action=db.permissions.TENANT_ALL,
                tenant_name=context.username,
            )
        region = os.getenv('AWS_REGION', 'eu-west-1')

        url = Quicksight.get_author_session(
            AwsAccountId=awsAccount,
            region=region,
            UserName=context.username,
            UserRole='AUTHOR',
        )

    return url


def get_quicksight_reader_session(context, source, dashboardId: str = None):
    with context.engine.scoped_session() as session:
        admin = TenantPolicy.is_tenant_admin(context.groups)

        if not admin:
            raise TenantUnauthorized(
                username=context.username,
                action=db.permissions.TENANT_ALL,
                tenant_name=context.username,
            )

        region = os.getenv('AWS_REGION', 'eu-west-1')
        current_account = SessionHelper.get_account()

        url = Quicksight.get_reader_session(
            AwsAccountId=current_account,
            region=region,
            UserName=context.username,
            UserRole='READER',
            DashboardId=dashboardId
        )

    return url
