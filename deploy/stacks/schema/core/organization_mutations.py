from awscdk.appsync_utils import ResolvableField
from injector import inject, singleton

from stacks.appsync import AppSyncStack
from stacks.schema import SchemaBase
from stacks.schema.core.organization_inputs import OrganizationInputs
from stacks.schema.core.organization_types import OrganizationTypes


@singleton
class OrganizationMutations(SchemaBase):
    @inject
    def __init__(
        self,
        org_inputs=OrganizationInputs(),
        org_types=OrganizationTypes(),
    ):
        schema = AppSyncStack.INSTANCE.schema
        data_source = AppSyncStack.INSTANCE.data_source

        schema.add_mutation(
            'createOrganization',
            ResolvableField(
                return_type=org_types.organization.attribute(),
                args={'input': org_inputs.new_organization_input.attribute()},
                data_source=data_source,
            ),
        )
