from aws_cdk.aws_appsync import GraphqlApi
from awscdk.appsync_utils import GraphqlType, EnumType, CodeFirstSchema, ObjectType
from injector import inject, singleton

from stacks.appsync import AppSyncStack
from stacks.schema import SchemaBase
from stacks.schema.commons import CommonTypes


@singleton
class OrganizationTypes(SchemaBase):
    @inject
    def __init__(
        self,
        common_types=CommonTypes(),
    ):
        schema = AppSyncStack.INSTANCE.schema

        self.organization_stats = ObjectType(
            'OrganizationStats',
            definition={
                'groups': GraphqlType.int(),
                'users': GraphqlType.int(),
                'environments': GraphqlType.int(),
            },
        )
        schema.add_type(self.organization_stats)

        self.organisation_user_role = EnumType(
            'OrganisationUserRole',
            definition=[
                'Owner',
                'Admin',
                'Member',
                'NotMember',
                'Invited',
            ],
        )
        schema.add_type(self.organisation_user_role)

        self.organization = ObjectType(
            'Organization',
            definition={
                'organizationUri': GraphqlType.id(),
                'label': GraphqlType.string(),
                'name': GraphqlType.string(),
                'description': GraphqlType.string(),
                'tags': GraphqlType.string(is_list=True),
                'owner': GraphqlType.string(),
                'SamlGroupName': GraphqlType.string(),
                # userRoleInOrganization: OrganisationUserRole
                # environments: EnvironmentSearchResult,
                'created': GraphqlType.string(),
                'updated': GraphqlType.string(),
                # stats: OrganizationStats
            },
        )
        schema.add_type(self.organization)

        self.organization_sort_field = EnumType(
            'OrganizationSortField',
            definition=[
                'created',
                'updated',
                'label',
            ],
        )
        schema.add_type(self.organization_sort_field)

        self.organization_search_result = ObjectType(
            'OrganizationSearchResult',
            interface_types=[common_types.paged_result],
            definition={'nodes': self.organization.attribute(is_list=True)},
        )
        schema.add_type(self.organization_search_result)
