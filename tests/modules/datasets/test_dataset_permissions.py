from dataall.base.context import set_context, RequestContext
from dataall.core.permissions.db.resource_policy import ResourcePolicy
from dataall.core.permissions.db.tenant import Tenant
from dataall.db.api import Environment, Organization
from dataall.db.exceptions import ResourceUnauthorized
from dataall.db.permissions import TENANT_ALL
from dataall.modules.datasets.services.dataset_permissions import DATASET_WRITE, UPDATE_DATASET, MANAGE_DATASETS, \
    DATASET_READ
from dataall.modules.datasets.services.dataset_service import DatasetService
from dataall.modules.datasets_base.db.models import Dataset
from dataall.modules.datasets_base.services.permissions import DATASET_TABLE_READ

from tests.db.test_permission import *


@pytest.fixture(scope='module', autouse=True)
def patch_methods(module_mocker):
    module_mocker.patch(
        'dataall.modules.datasets.services.dataset_service.DatasetService._deploy_dataset_stack',
        return_value=True
    )


@pytest.fixture(scope='module')
def tenant(db):
    with db.scoped_session() as session:
        tenant = Tenant.save_tenant(
            session, name='dataall', description='Tenant dataall'
        )
        yield tenant


@pytest.fixture(scope='module', autouse=True)
def dataset(org, env, db, group):
    with db.scoped_session() as session:
        dataset = Dataset(
            organizationUri=org.organizationUri,
            environmentUri=env.environmentUri,
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
        session.add(dataset)
    yield dataset


def test_attach_resource_policy(db, user, group, dataset):
    permissions(db, ENVIRONMENT_ALL + ORGANIZATION_ALL + DATASET_READ + DATASET_WRITE + DATASET_TABLE_READ)
    with db.scoped_session() as session:
        ResourcePolicy.attach_resource_policy(
            session=session,
            group=group.name,
            permissions=DATASET_WRITE,
            resource_uri=dataset.datasetUri,
            resource_type=Dataset.__name__,
        )
        assert ResourcePolicy.check_user_resource_permission(
            session=session,
            username=user.userName,
            groups=[group.name],
            permission_name=UPDATE_DATASET,
            resource_uri=dataset.datasetUri,
        )


def test_attach_tenant_policy(
    db, user, group, group_user, dataset, permissions, tenant
):
    with db.scoped_session() as session:
        TenantPolicy.attach_group_tenant_policy(
            session=session,
            group=group.name,
            permissions=[MANAGE_DATASETS],
            tenant_name='dataall',
        )

        assert TenantPolicy.check_user_tenant_permission(
            session=session,
            username=user.userName,
            groups=[group.name],
            permission_name=MANAGE_DATASETS,
            tenant_name='dataall',
        )


def test_unauthorized_resource_policy(
    db, user, group_user, group, dataset, permissions
):
    with pytest.raises(ResourceUnauthorized):
        with db.scoped_session() as session:
            assert ResourcePolicy.check_user_resource_permission(
                session=session,
                username=user.userName,
                groups=[group.name],
                permission_name='UNKNOWN_PERMISSION',
                resource_uri=dataset.datasetUri,
            )


def test_create_dataset(db, env, user, group, group_user, dataset, permissions, tenant):
    with db.scoped_session() as session:
        set_context(RequestContext(db, user.userName, [group.name]))

        TenantPolicy.attach_group_tenant_policy(
            session=session,
            group=group.name,
            permissions=TENANT_ALL,
            tenant_name='dataall',
        )
        org_with_perm = Organization.create_organization(
            session=session,
            data={
                'label': 'OrgWithPerm',
                'SamlGroupName': group.name,
                'description': 'desc',
                'tags': [],
            },
        )
        env_with_perm = Environment.create_environment(
            session=session,
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
