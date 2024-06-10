from assertpy import assert_that

from .queries import (
    archive_organization,
    create_organization,
    get_organization,
    invite_team_to_organization,
    list_organizations,
    remove_team_from_organization,
    update_organization,
)


def test_create_organization_with_team_with_permissions(organization1):
    # Given a user with permissions
    # When we create the fixture organization
    organization = organization1
    # Then
    assert_that(organization.organizationUri).is_length(8)
    assert_that(organization.label).is_equal_to('organization1')


def test_create_organization_with_unauthorized_team(client_noTenantPermissions, group4):
    # Given a user with no tenant permissions to MANAGE ORGANIZATIONS
    # When it creates an organization
    response = create_organization(client_noTenantPermissions, 'organization2', group4)
    # Then
    assert_that(response.errors[0].message).contains('UnauthorizedOperation', 'MANAGE_ORGANIZATIONS')


def test_get_organization_organization_with_admin_team(client1, organization1):
    # Given
    organization = organization1
    # When
    response = get_organization(client=client1, organizationUri=organization.organizationUri)
    # Then
    assert_that(response.data.getOrganization.organizationUri).is_equal_to(organization.organizationUri)
    assert_that(response.data.getOrganization.owner).is_equal_to(organization.owner)
    assert_that(response.data.getOrganization.SamlGroupName).is_equal_to(organization.SamlGroupName)
    assert_that(response.data.getOrganization.userRoleInOrganization).is_equal_to('Owner')
    assert_that(response.data.getOrganization.stats.groups).is_equal_to(0)


def test_get_organization_organization_with_invited_team(client2, organization2_with_invited_group2):
    # Given an organization
    organization = organization2_with_invited_group2
    # When an invited team (client2) gets the organization
    response = get_organization(client=client2, organizationUri=organization.organizationUri)
    # Then
    assert_that(response.data.getOrganization.organizationUri).is_equal_to(organization.organizationUri)
    assert_that(response.data.getOrganization.userRoleInOrganization).is_equal_to('Invited')
    assert_that(response.data.getOrganization.stats.groups).is_equal_to(1)


def test_get_organization_with_unauthorized_team(client3, organization1):
    # Given an organization
    organization = organization1
    # When an unauthorized (client3) gets the organization
    response = get_organization(client=client3, organizationUri=organization.organizationUri)
    # Then
    assert_that(response.errors[0].message).contains(
        'UnauthorizedOperation', 'GET_ORGANIZATION', organization.organizationUri
    )


def test_list_organizations_with_admin_team(client1, organization1, organization2_with_invited_group2):
    # Given 2 organizations
    # When the admin user of both of them
    response = list_organizations(client1)
    # Then
    assert_that(response.data.listOrganizations.count).is_equal_to(2)


def test_list_organizations_with_invited_team(client2, organization1, organization2_with_invited_group2):
    # Given 2 organizations
    # When an invited user to one organization only
    response = list_organizations(client2)
    # Then
    assert_that(response.data.listOrganizations.count).is_equal_to(1)


def test_list_organizations_with_unauthorized_team(client3, organization1, organization2_with_invited_group2):
    # Given 2 organizations
    # When a non-invited user
    response = list_organizations(client3)
    # Then
    assert_that(response.data.listOrganizations.count).is_equal_to(0)


def test_update_organization_organization_with_admin_team(client1, organization1):
    # Given an organization
    organization = organization1
    # When the admin team (client1) updates the organization
    response = update_organization(client=client1, organizationUri=organization.organizationUri)
    # Then
    assert_that(response.data.updateOrganization.owner).is_equal_to(organization.owner)
    assert_that(response.data.updateOrganization.SamlGroupName).is_equal_to(organization.SamlGroupName)
    assert_that(response.data.updateOrganization.label).is_equal_to('newlabel')


def test_update_organization_organization_with_unauthorized_team(client3, organization1):
    # Given an organization
    organization = organization1
    # When an unauthorized (client3) updates the organization
    response = update_organization(client=client3, organizationUri=organization.organizationUri)
    # Then
    assert_that(response.errors[0].message).contains(
        'UnauthorizedOperation', 'UPDATE_ORGANIZATION', organization.organizationUri
    )


def test_invite_group_to_organization_with_admin_team(organization2_with_invited_group2):
    # Given a user with permissions that has created an organization
    organization = organization2_with_invited_group2
    # When we create the fixture
    # Then
    assert_that(organization.organizationUri).is_length(8)
    assert_that(organization.label).is_equal_to('organization2')


def test_invite_group_to_organization_with_unauthorized_team(client3, organization1, group2):
    # Given an organization
    organization = organization1
    # When an unauthorized (client3) invites a team to the organization
    response = invite_team_to_organization(client=client3, organizationUri=organization.organizationUri, group=group2)
    # Then
    assert_that(response.errors[0].message).contains(
        'UnauthorizedOperation', 'INVITE_ORGANIZATION_GROUP', organization.organizationUri
    )


def test_remove_group_from_organization_with_admin_team(client1, organization2_with_invited_group2, group2):
    # Given an organization
    organization = organization2_with_invited_group2
    # When the admin team (client1) removes a team from the organization
    response = remove_team_from_organization(client=client1, organizationUri=organization.organizationUri, group=group2)
    # Then
    assert_that(response.data.removeGroupFromOrganization.organizationUri).is_equal_to(organization.organizationUri)


def test_remove_group_from_organization_with_unauthorized_team(client3, organization2_with_invited_group2, group2):
    # Given an organization
    organization = organization2_with_invited_group2
    # When an unauthorized (client3) removes a team from the organization
    response = remove_team_from_organization(client=client3, organizationUri=organization.organizationUri, group=group2)
    # Then
    assert_that(response.errors[0].message).contains(
        'UnauthorizedOperation', 'REMOVE_ORGANIZATION_GROUP', organization.organizationUri
    )


def test_archive_organization_organization_with_admin_team(client1, organization1):
    # Given an organization
    organization = organization1
    # When admin team (client1) archives the organization
    response = archive_organization(client=client1, organizationUri=organization.organizationUri)
    # Then
    assert_that(response.data.archiveOrganization).is_true()


def test_archive_organization_organization_with_invited_team(client2, organization2_with_invited_group2):
    # Given an organization
    organization = organization2_with_invited_group2
    # When an invited team, unauthorized (client2) archives the organization
    response = archive_organization(client=client2, organizationUri=organization.organizationUri)
    # Then
    assert_that(response.errors[0].message).contains(
        'UnauthorizedOperation', 'DELETE_ORGANIZATION', organization.organizationUri
    )


def test_archive_organization_organization_with_unauthorized_team(client3, organization1):
    # Given an organization
    organization = organization1
    # When an unauthorized (client3) archives the organization
    response = archive_organization(client=client3, organizationUri=organization.organizationUri)
    # Then
    assert_that(response.errors[0].message).contains(
        'UnauthorizedOperation', 'DELETE_ORGANIZATION', organization.organizationUri
    )


# TODO: list_organization_environments as part of environment tests
