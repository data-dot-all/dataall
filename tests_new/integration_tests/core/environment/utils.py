from integration_tests.core.environment.queries import update_environment
from integration_tests.core.stack.utils import check_stack_ready, check_stack_in_progress
from integration_tests.core.stack.queries import update_stack


def set_env_params(client, env, **new_params):
    should_update = False
    new_params_list = []
    for param in env.parameters:
        new_param_value = new_params.get(param.key, param.value)
        if new_param_value != param.value:
            should_update = True
        new_params_list.append({'key': param.key, 'value': new_param_value})
    if should_update:
        env_uri = env.environmentUri
        stack_uri = env.stack.stackUri
        check_stack_ready(client, env_uri, stack_uri)
        update_environment(
            client,
            env.environmentUri,
            {
                k: v
                for k, v in env.items()
                if k
                in [
                    'description',
                    'label',
                    'resourcePrefix',
                    'subnetIds',
                    'tags',
                    'vpcId',
                ]
            }
            | {'parameters': new_params_list},
        )
        check_stack_in_progress(client, env_uri, stack_uri)
        check_stack_ready(client, env_uri, stack_uri)


def update_env_stack(client, env):
    stack_uri = env.stack.stackUri
    env_uri = env.environmentUri
    # wait for stack to get to a final state before triggering an update
    check_stack_ready(client, env_uri, stack_uri)
    update_stack(client, env_uri, 'environment')
    # wait for stack to move to "in_progress" state
    check_stack_in_progress(client, env_uri, stack_uri)
    return check_stack_ready(client, env_uri, stack_uri)
