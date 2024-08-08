from dataall.base.context import set_context, RequestContext
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.base.db.exceptions import ResourceUnauthorized
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.modules.s3_datasets.services.dataset_permissions import (
    DATASET_WRITE,
    UPDATE_DATASET,
    MANAGE_DATASETS,
    DATASET_READ,
)
from dataall.modules.s3_datasets.services.dataset_service import DatasetService
from dataall.modules.datasets_base.db.dataset_models import DatasetBase
from dataall.modules.s3_datasets.services.dataset_permissions import DATASET_TABLE_ALL

from tests.core.permissions.test_permission import *
from dataall.core.organizations.services.organization_service import OrganizationService
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService


def test_attach_resource_policy(db, user, group, dataset_fixture):
    permissions(db, ENVIRONMENT_ALL + ORGANIZATION_ALL + DATASET_READ + DATASET_WRITE + DATASET_TABLE_ALL)
    with db.scoped_session() as session:
        ResourcePolicyService.attach_resource_policy(
            session=session,
            group=group.name,
            permissions=DATASET_WRITE,
            resource_uri=dataset_fixture.datasetUri,
            resource_type=DatasetBase.__name__,
        )
        assert ResourcePolicyService.check_user_resource_permission(
            session=session,
            username=user.username,
            groups=[group.name],
            permission_name=UPDATE_DATASET,
            resource_uri=dataset_fixture.datasetUri,
        )


def test_attach_tenant_policy(db, user, group, dataset_fixture, permissions, tenant):
    with db.scoped_session() as session:
        TenantPolicyService.attach_group_tenant_policy(
            session=session,
            group=group.name,
            permissions=[MANAGE_DATASETS],
            tenant_name='dataall',
        )

        assert TenantPolicyService.check_user_tenant_permission(
            session=session,
            username=user.username,
            groups=[group.name],
            permission_name=MANAGE_DATASETS,
            tenant_name='dataall',
        )


def test_unauthorized_resource_policy(db, user, group, dataset_fixture, permissions):
    with pytest.raises(ResourceUnauthorized):
        with db.scoped_session() as session:
            assert ResourcePolicyService.check_user_resource_permission(
                session=session,
                username=user.username,
                groups=[group.name],
                permission_name='UNKNOWN_PERMISSION',
                resource_uri=dataset_fixture.datasetUri,
            )


def test_create_dataset(db, user, group, dataset_fixture, permissions, tenant):
    with db.scoped_session() as session:
        set_context(RequestContext(db, user.username, [group.name], user_id=user.username))

        TenantPolicyService.attach_group_tenant_policy(
            session=session,
            group=group.name,
            permissions=TENANT_ALL,
            tenant_name=TenantPolicyService.TENANT_NAME,
        )
        org_with_perm = OrganizationService.create_organization(
            data={
                'label': 'OrgWithPerm',
                'SamlGroupName': group.name,
                'description': 'desc',
                'tags': [],
            },
        )
        env_with_perm = EnvironmentService.create_environment(
            uri=org_with_perm.organizationUri,
            data={
                'label': 'EnvWithPerm',
                'organizationUri': org_with_perm.organizationUri,
                'SamlGroupName': group.name,
                'description': 'desc',
                'AwsAccountId': '123456789012',
                'region': 'eu-west-1',
                'cdk_role_name': 'cdkrole',
            },
        )

        data = dict(
            label='label',
            owner='foo',
            SamlAdminGroupName=group.name,
            businessOwnerDelegationEmails=['foo@amazon.com'],
            businessOwnerEmail=['bar@amazon.com'],
            name='name',
            S3BucketName='S3BucketName',
            GlueDatabaseName='GlueDatabaseName',
            KmsAlias='kmsalias',
            AwsAccountId='123456789012',
            region='eu-west-1',
            IAMDatasetAdminUserArn=f'arn:aws:iam::123456789012:user/dataset',
            IAMDatasetAdminRoleArn=f'arn:aws:iam::123456789012:role/dataset',
        )

        dataset = DatasetService.create_dataset(
            uri=env_with_perm.environmentUri,
            admin_group=group.name,
            data=data,
        )
        assert dataset
