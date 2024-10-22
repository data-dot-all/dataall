from assertpy import assert_that

from integration_tests.core.organizations.queries import (
    archive_organization,
    create_organization,
    get_organization,
    invite_team_to_organization,
    list_organizations,
    remove_team_from_organization,
    update_organization,
)
from integration_tests.errors import GqlError


def test_create_organization_with_team_with_permissions(org1):
    # Given a user with permissions
    # When we create the fixture organization
    organization = org1
    # Then
    assert_that(organization.organizationUri).is_length(8)
    assert_that(organization.label).is_equal_to('organization1')


def test_create_organization_with_unauthorized_team(client_noTenantPermissions, group4):
    # Given a user with no tenant permissions to MANAGE ORGANIZATIONS
    # When it creates an organization
    assert_that(create_organization).raises(GqlError).when_called_with(
        client_noTenantPermissions,
        'organization2',
        group4,
    ).contains('UnauthorizedOperation', 'MANAGE_ORGANIZATIONS')


def test_get_organization_organization_with_admin_team(client1, org1):
    # Given
    organization = org1
    # When
    response = get_organization(client=client1, organizationUri=organization.organizationUri)
    # Then
    assert_that(response.organizationUri).is_equal_to(organization.organizationUri)
    assert_that(response.owner).is_equal_to(organization.owner)
    assert_that(response.SamlGroupName).is_equal_to(organization.SamlGroupName)
    assert_that(response.userRoleInOrganization).is_equal_to('Owner')


def test_get_organization_with_invited_team(client2, org2):
    # Given an organization
    organization = org2
    # When an invited team (client2) gets the organization
    response = get_organization(client=client2, organizationUri=organization.organizationUri)
    # Then
    assert_that(response.organizationUri).is_equal_to(organization.organizationUri)
    assert_that(response.userRoleInOrganization).is_equal_to('Invited')
    assert_that(response.stats.groups).is_equal_to(2)


def test_get_organization_with_unauthorized_team(client3, org1):
    assert_that(get_organization).raises(GqlError).when_called_with(
        client=client3,
        organizationUri=org1.organizationUri,
    ).contains(
        'UnauthorizedOperation',
        'GET_ORGANIZATION',
        org1.organizationUri,
    )


def test_list_organizations_with_admin_team(client1, org1, org2, session_id):
    # Given 2 organizations
    # When the admin user of both of them
    response = list_organizations(client1, term=session_id)
    # Then
    assert_that(response.count).is_equal_to(2)


def test_list_organizations_with_invited_team(client2, org1, org2, session_id):
    # Given 2 organizations
    # When an invited user to one organization only
    response = list_organizations(client2, term=session_id)
    # Then
    assert_that(response.count).is_equal_to(1)


def test_list_organizations_with_unauthorized_team(client4, org1, org2, session_id):
    # Given 2 organizations
    # When a non-invited user
    response = list_organizations(client4, term=session_id)
    # Then
    assert_that(response.count).is_equal_to(0)


def test_update_organization_organization_with_admin_team(client1, org1):
    # Given an organization
    organization = org1
    # When the admin team (client1) updates the organization
    response = update_organization(client=client1, organizationUri=organization.organizationUri)
    # Then
    assert_that(response.owner).is_equal_to(organization.owner)
    assert_that(response.SamlGroupName).is_equal_to(organization.SamlGroupName)
    assert_that(response.label).is_equal_to('newlabel')


def test_update_organization_organization_with_unauthorized_team(client3, org1):
    assert_that(update_organization).raises(GqlError).when_called_with(
        client=client3,
        organizationUri=org1.organizationUri,
    ).contains(
        'UnauthorizedOperation',
        'UPDATE_ORGANIZATION',
        org1.organizationUri,
    )


def test_invite_group_to_organization_with_admin_team(org2):
    # Given a user with permissions that has created an organization
    organization = org2
    # When we create the fixture
    # Then
    assert_that(organization.organizationUri).is_length(8)
    assert_that(organization.label).is_equal_to('organization2')


def test_invite_group_to_organization_with_unauthorized_team(client3, org1, group2):
    assert_that(invite_team_to_organization).raises(GqlError).when_called_with(
        client=client3,
        organizationUri=org1.organizationUri,
        group=group2,
    ).contains(
        'UnauthorizedOperation',
        'INVITE_ORGANIZATION_GROUP',
        org1.organizationUri,
    )


def test_remove_group_from_organization_with_admin_team(client1, org2, group2):
    # Given an organization
    organization = org2
    # When the admin team (client1) removes a team from the organization
    response = remove_team_from_organization(client=client1, organizationUri=organization.organizationUri, group=group2)
    # Then
    assert_that(response.organizationUri).is_equal_to(organization.organizationUri)


def test_remove_group_from_organization_with_unauthorized_team(client3, org2, group2):
    assert_that(remove_team_from_organization).raises(GqlError).when_called_with(
        client=client3,
        organizationUri=org2.organizationUri,
        group=group2,
    ).contains(
        'UnauthorizedOperation',
        'REMOVE_ORGANIZATION_GROUP',
        org2.organizationUri,
    )


def test_archive_organization_organization_with_admin_team(client1, group1):
    # Given an organization
    organization = create_organization(client1, 'testArchiveFromAdmin', group1)
    # When admin team (client1) archives the organization
    response = archive_organization(client=client1, organizationUri=organization.organizationUri)
    # Then
    assert_that(response).is_true()


def test_archive_organization_organization_with_invited_team(client2, org2):
    assert_that(archive_organization).raises(GqlError).when_called_with(
        client=client2,
        organizationUri=org2.organizationUri,
    ).contains(
        'UnauthorizedOperation',
        'DELETE_ORGANIZATION',
        org2.organizationUri,
    )


def test_archive_organization_organization_with_unauthorized_team(client3, org1):
    assert_that(archive_organization).raises(GqlError).when_called_with(
        client=client3,
        organizationUri=org1.organizationUri,
    ).contains(
        'UnauthorizedOperation',
        'DELETE_ORGANIZATION',
        org1.organizationUri,
    )


# TODO: list_organization_environments as part of environment tests
