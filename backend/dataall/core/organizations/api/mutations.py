from dataall.base.api import gql
from .input_types import (
    ModifyOrganizationInput,
    NewOrganizationInput,
    InviteGroupToOrganizationInput,
)
from .resolvers import (
    archive_organization,
    create_organization,
    invite_group,
    remove_group,
    update_organization,
    update_group,
)
from .types import Organization

createOrganization = gql.MutationField(
    name='createOrganization',
    args=[gql.Argument(name='input', type=NewOrganizationInput)],
    type=gql.Thunk(lambda: Organization),
    resolver=create_organization,
    test_scope='Organization',
)

updateOrganization = gql.MutationField(
    name='updateOrganization',
    args=[
        gql.Argument(name='organizationUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='input', type=gql.NonNullableType(ModifyOrganizationInput)),
    ],
    type=gql.Thunk(lambda: Organization),
    resolver=update_organization,
    test_scope='Organization',
)

archiveOrganization = gql.MutationField(
    name='archiveOrganization',
    args=[gql.Argument(name='organizationUri', type=gql.NonNullableType(gql.String))],
    resolver=archive_organization,
    type=gql.Boolean,
)

inviteGroupToOrganization = gql.MutationField(
    name='inviteGroupToOrganization',
    args=[gql.Argument(name='input', type=gql.NonNullableType(InviteGroupToOrganizationInput))],
    type=gql.Ref('Organization'),
    resolver=invite_group,
)

updateOrganizationGroup = gql.MutationField(
    name='updateOrganizationGroup',
    args=[gql.Argument(name='input', type=gql.NonNullableType(InviteGroupToOrganizationInput))],
    type=gql.Ref('Organization'),
    resolver=update_group,
)

removeGroupFromOrganization = gql.MutationField(
    name='removeGroupFromOrganization',
    args=[
        gql.Argument('organizationUri', type=gql.NonNullableType(gql.String)),
        gql.Argument('groupUri', type=gql.NonNullableType(gql.String)),
    ],
    type=gql.Ref('Organization'),
    resolver=remove_group,
)
