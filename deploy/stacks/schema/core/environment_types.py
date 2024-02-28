from aws_cdk.aws_appsync import GraphqlApi
from awscdk.appsync_utils import GraphqlType, EnumType, CodeFirstSchema, ObjectType
from injector import inject, singleton

from stacks.schema import SchemaBase
from stacks.schema.commons import CommonTypes


@singleton
class EnvironmentTypes(SchemaBase):
    @inject
    def __init__(self, api: GraphqlApi, common_types: CommonTypes):
        schema: CodeFirstSchema = api.schema

        self.environment_permission = EnumType('EnvironmentPermission', definition=[
            'Owner',
            'Admin',
            'DatasetCreator',
            'Invited',
            'ProjectAccess',
            'NotInvited',
        ])
        schema.add_type(self.environment_permission)

        self.environment_sort_field = EnumType('EnvironmentSortField', definition=[
            'created',
            'updated',
            'label',
        ])
        schema.add_type(self.environment_sort_field)

        environment = ObjectType('Environment', definition={
            'environmentUri': GraphqlType.id(),
            'label': GraphqlType.string(),
            'name': GraphqlType.string(),
            'description': GraphqlType.string(),
            'tags': GraphqlType.string(is_list=True),
            'owner': GraphqlType.string(),
            'created': GraphqlType.string(),
            'updated': GraphqlType.string(),
            'SamlGroupName': GraphqlType.string(),
            'userRoleInEnvironment': self.environment_permission.attribute(),
            'AwsAccountId': GraphqlType.string(),
            'region': GraphqlType.string(),
        })
        schema.add_type(environment)

        self.environment_search_result = ObjectType('EnvironmentSearchResult', interface_types=[common_types.paged_result], definition={
            'nodes': environment.attribute(is_list=True),
        })
        schema.add_type(self.environment_search_result)
