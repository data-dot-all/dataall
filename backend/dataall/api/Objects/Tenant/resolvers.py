import os

from .... import db
from ....aws.handlers.sts import SessionHelper
from ....aws.handlers.parameter_store import ParameterStoreManager
from ....aws.handlers.quicksight import Quicksight
from ....db import exceptions


def update_group_permissions(context, source, input=None):
    with context.engine.scoped_session() as session:
        return db.api.TenantPolicy.update_group_permissions(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=input['groupUri'],
            data=input,
            check_perm=True,
        )


def list_tenant_permissions(context, source):
    with context.engine.scoped_session() as session:
        return db.api.TenantPolicy.list_tenant_permissions(
            session=session, username=context.username, groups=context.groups
        )


def list_tenant_groups(context, source, filter=None):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return db.api.TenantPolicy.list_tenant_groups(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=None,
            data=filter,
            check_perm=True,
        )


def update_ssm_parameter(context, source, name: str = None, value: str = None):
    current_account = SessionHelper.get_account()
    region = os.getenv('AWS_REGION', 'eu-west-1')
    print(value)
    print(name)
    response = ParameterStoreManager.update_parameter(AwsAccountId=current_account, region=region, parameter_name=f'/dataall/{os.getenv("envname", "local")}/quicksightmonitoring/{name}', parameter_value=value)
    return response


def get_monitoring_dashboard_id(context, source):
    current_account = SessionHelper.get_account()
    region = os.getenv('AWS_REGION', 'eu-west-1')
    dashboard_id = ParameterStoreManager.get_parameter_value(AwsAccountId=current_account, region=region, parameter_path=f'/dataall/{os.getenv("envname", "local")}/quicksightmonitoring/DashboardId')
    if not dashboard_id:
        raise exceptions.AWSResourceNotFound(
            action='GET_DASHBOARD_ID',
            message='Dashboard Id could not be found on AWS Parameter Store',
        )
    return dashboard_id


def get_monitoring_vpc_connection_id(context, source):
    current_account = SessionHelper.get_account()
    region = os.getenv('AWS_REGION', 'eu-west-1')
    vpc_connection_id = ParameterStoreManager.get_parameter_value(AwsAccountId=current_account, region=region, parameter_path=f'/dataall/{os.getenv("envname", "local")}/quicksightmonitoring/VPCConnectionId')
    if not vpc_connection_id:
        raise exceptions.AWSResourceNotFound(
            action='GET_VPC_CONNECTION_ID',
            message='Dashboard Id could not be found on AWS Parameter Store',
        )
    return vpc_connection_id


def create_quicksight_data_source_set(context, source, vpcConnectionId: str = None):
    current_account = SessionHelper.get_account()
    region = os.getenv('AWS_REGION', 'eu-west-1')
    user = Quicksight.register_user_in_group(AwsAccountId=current_account, UserName=context.username, GroupName='dataall', UserRole='AUTHOR')

    datasourceId = Quicksight.create_data_source_vpc(AwsAccountId=current_account, region=region, UserName=context.username, vpcConnectionId=vpcConnectionId)
    # Data sets are not created programmatically. Too much overhead for the value added. However, an example API is provided:
    # datasets = Quicksight.create_data_set_from_source(AwsAccountId=current_account, region=region, UserName='dataallTenantUser', dataSourceId=datasourceId, tablesToImport=['organization', 'environment', 'dataset', 'datapipeline', 'dashboard', 'share_object'])

    return datasourceId


def get_quicksight_author_session(context, source, awsAccount: str = None):
    with context.engine.scoped_session() as session:
        admin = db.api.TenantPolicy.is_tenant_admin(context.groups)

        if not admin:
            raise db.exceptions.TenantUnauthorized(
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
        admin = db.api.TenantPolicy.is_tenant_admin(context.groups)

        if not admin:
            raise db.exceptions.TenantUnauthorized(
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
