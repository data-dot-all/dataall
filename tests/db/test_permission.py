import pytest

import dataall
from dataall.api.constants import OrganisationUserRole
from dataall.db import exceptions
from dataall.db.models.Permission import PermissionType


@pytest.fixture(scope="module")
def permissions(db):
    with db.scoped_session() as session:
        permissions = []
        for p in (
            dataall.db.permissions.DATASET_READ
            + dataall.db.permissions.DATASET_WRITE
            + dataall.db.permissions.ORGANIZATION_ALL
            + dataall.db.permissions.ENVIRONMENT_ALL
        ):
            permissions.append(
                dataall.db.api.Permission.save_permission(
                    session,
                    name=p,
                    description=p,
                    permission_type=PermissionType.RESOURCE.name,
                )
            )
        for p in dataall.db.permissions.TENANT_ALL:
            permissions.append(
                dataall.db.api.Permission.save_permission(
                    session,
                    name=p,
                    description=p,
                    permission_type=PermissionType.TENANT.name,
                )
            )
        session.commit()
        yield permissions


@pytest.fixture(scope="module")
def tenant(db):
    with db.scoped_session() as session:
        tenant = dataall.db.api.Tenant.save_tenant(session, name="dataall", description="Tenant dataall")
        yield tenant


@pytest.fixture(scope="module")
def user(db):
    with db.scoped_session() as session:
        user = dataall.db.models.User(userId="alice@test.com", userName="alice")
        session.add(user)
        yield user


@pytest.fixture(scope="module")
def group(db, user):
    with db.scoped_session() as session:
        group = dataall.db.models.Group(name="testadmins", label="testadmins", owner="alice")
        session.add(group)
        yield group


@pytest.fixture(scope="module")
def group_user(db, group, user):
    with db.scoped_session() as session:
        member = dataall.db.models.GroupMember(
            userName=user.userName,
            groupUri=group.groupUri,
        )
        session.add(member)
        yield member


@pytest.fixture(scope="module", autouse=True)
def org(db, group):
    with db.scoped_session() as session:
        org = dataall.db.models.Organization(
            label="org",
            owner="alice",
            tags=[],
            description="desc",
            SamlGroupName=group.name,
            userRoleInOrganization=OrganisationUserRole.Owner.value,
        )
        session.add(org)
    yield org


@pytest.fixture(scope="module", autouse=True)
def env(org, db, group):
    with db.scoped_session() as session:
        env = dataall.db.models.Environment(
            organizationUri=org.organizationUri,
            AwsAccountId="12345678901",
            region="eu-west-1",
            label="org",
            owner="alice",
            tags=[],
            description="desc",
            SamlGroupName=group.name,
            EnvironmentDefaultIAMRoleName="EnvRole",
            EnvironmentDefaultIAMRoleArn="arn:aws::123456789012:role/EnvRole/GlueJobSessionRunner",
            CDKRoleArn="arn:aws::123456789012:role/EnvRole",
            userRoleInEnvironment="999",
        )
        session.add(env)
    yield env


@pytest.fixture(scope="module", autouse=True)
def dataset(org, env, db, group):
    with db.scoped_session() as session:
        dataset = dataall.db.models.Dataset(
            organizationUri=org.organizationUri,
            environmentUri=env.environmentUri,
            label="label",
            owner="foo",
            SamlAdminGroupName=group.name,
            businessOwnerDelegationEmails=["foo@amazon.com"],
            businessOwnerEmail=["bar@amazon.com"],
            name="name",
            S3BucketName="S3BucketName",
            GlueDatabaseName="GlueDatabaseName",
            KmsAlias="kmsalias",
            AwsAccountId="123456789012",
            region="eu-west-1",
            IAMDatasetAdminUserArn=f"arn:aws:iam::123456789012:user/dataset",
            IAMDatasetAdminRoleArn=f"arn:aws:iam::123456789012:role/dataset",
        )
        session.add(dataset)
    yield dataset


def test_attach_resource_policy(db, user, group, group_user, dataset, permissions):
    with db.scoped_session() as session:

        dataall.db.api.ResourcePolicy.attach_resource_policy(
            session=session,
            group=group.name,
            permissions=dataall.db.permissions.DATASET_WRITE,
            resource_uri=dataset.datasetUri,
            resource_type=dataall.db.models.Dataset.__name__,
        )
        assert dataall.db.api.ResourcePolicy.check_user_resource_permission(
            session=session,
            username=user.userName,
            groups=[group.name],
            permission_name=dataall.db.permissions.UPDATE_DATASET,
            resource_uri=dataset.datasetUri,
        )


def test_attach_tenant_policy(db, user, group, group_user, dataset, permissions, tenant):
    with db.scoped_session() as session:

        dataall.db.api.TenantPolicy.attach_group_tenant_policy(
            session=session,
            group=group.name,
            permissions=[dataall.db.permissions.MANAGE_DATASETS],
            tenant_name="dataall",
        )

        assert dataall.db.api.TenantPolicy.check_user_tenant_permission(
            session=session,
            username=user.userName,
            groups=[group.name],
            permission_name=dataall.db.permissions.MANAGE_DATASETS,
            tenant_name="dataall",
        )


def test_unauthorized_resource_policy(db, user, group_user, group, dataset, permissions):
    with pytest.raises(exceptions.ResourceUnauthorized):
        with db.scoped_session() as session:
            assert dataall.db.api.ResourcePolicy.check_user_resource_permission(
                session=session,
                username=user.userName,
                groups=[group.name],
                permission_name="UNKNOW_PERMISSION",
                resource_uri=dataset.datasetUri,
            )


def test_unauthorized_tenant_policy(db, user, group, group_user, dataset, permissions, tenant):
    with pytest.raises(exceptions.TenantUnauthorized):
        with db.scoped_session() as session:
            assert dataall.db.api.TenantPolicy.check_user_tenant_permission(
                session=session,
                username=user.userName,
                groups=[group.name],
                permission_name="UNKNOW_PERMISSION",
                tenant_name="dataall",
            )


def test_create_dataset(db, env, user, group, group_user, dataset, permissions, tenant):
    with db.scoped_session() as session:
        dataall.db.api.TenantPolicy.attach_group_tenant_policy(
            session=session,
            group=group.name,
            permissions=dataall.db.permissions.TENANT_ALL,
            tenant_name="dataall",
        )
        org_with_perm = dataall.db.api.Organization.create_organization(
            session=session,
            username=user.userName,
            groups=[group.name],
            uri=None,
            data={
                "label": "OrgWithPerm",
                "SamlGroupName": group.name,
                "description": "desc",
                "tags": [],
            },
            check_perm=True,
        )
        env_with_perm = dataall.db.api.Environment.create_environment(
            session=session,
            username=user.userName,
            groups=[group.name],
            uri=org_with_perm.organizationUri,
            data={
                "label": "EnvWithPerm",
                "organizationUri": org_with_perm.organizationUri,
                "SamlGroupName": group.name,
                "description": "desc",
                "AwsAccountId": "123456789012",
                "region": "eu-west-1",
                "cdk_role_name": "cdkrole",
            },
            check_perm=True,
        )

        data = dict(
            label="label",
            owner="foo",
            SamlAdminGroupName=group.name,
            businessOwnerDelegationEmails=["foo@amazon.com"],
            businessOwnerEmail=["bar@amazon.com"],
            name="name",
            S3BucketName="S3BucketName",
            GlueDatabaseName="GlueDatabaseName",
            KmsAlias="kmsalias",
            AwsAccountId="123456789012",
            region="eu-west-1",
            IAMDatasetAdminUserArn=f"arn:aws:iam::123456789012:user/dataset",
            IAMDatasetAdminRoleArn=f"arn:aws:iam::123456789012:role/dataset",
        )
        dataset = dataall.db.api.Dataset.create_dataset(
            session=session,
            username=user.userName,
            groups=[group.name],
            uri=env_with_perm.environmentUri,
            data=data,
            check_perm=True,
        )
        assert dataset
