from awscdk.appsync_utils import ResolvableField

from stacks.appsync import AppSyncStack
from stacks.schema.core.organization_inputs import OrganizationInputs
from stacks.schema.core.organization_types import OrganizationTypes


class OrganizationMutations:
    def __init__(
        self,
        app_sync_stack: AppSyncStack,
        org_inputs: OrganizationInputs,
        org_types: OrganizationTypes,
        **_kwargs,
    ):
        app_sync_stack.schema.add_mutation(
            'createOrganization',
            ResolvableField(
                return_type=org_types.organization.attribute(),
                args={'input': org_inputs.new_organization_input.attribute()},
                data_source=app_sync_stack.data_source,
            ),
        )
