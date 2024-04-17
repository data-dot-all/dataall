from stacks import schema
from stacks.schema.commons import CommonTypes
from stacks.schema.core.environment_inputs import EnvironmentInputs
from stacks.schema.core.environment_queries import EnvironmentQueries
from stacks.schema.core.environment_types import EnvironmentTypes
from stacks.schema.core.organization_inputs import OrganizationInputs
from stacks.schema.core.organization_mutations import OrganizationMutations
from stacks.schema.core.organization_queries import OrganizationQueries
from stacks.schema.core.organization_types import OrganizationTypes
from stacks.schema.core.stack_queries import StackQueries
from stacks.schema.core.stack_types import StackTypes


def create_schema(app_sync_stack):
    kwargs = {'app_sync_stack': app_sync_stack}
    kwargs['common_types'] = CommonTypes(**kwargs)
    kwargs['env_types'] = EnvironmentTypes(**kwargs)
    kwargs['org_types'] = OrganizationTypes(**kwargs)
    kwargs['stack_types'] = StackTypes(**kwargs)

    kwargs['env_inputs'] = EnvironmentInputs(**kwargs)
    kwargs['env_queries'] = EnvironmentQueries(**kwargs)
    kwargs['org_inputs'] = OrganizationInputs(**kwargs)
    kwargs['org_queries'] = OrganizationQueries(**kwargs)
    kwargs['org_mutations'] = OrganizationMutations(**kwargs)

    kwargs['stack_queries'] = StackQueries(**kwargs)
