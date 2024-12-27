from integration_tests.core.environment.queries import update_environment
from integration_tests.core.stack.utils import check_stack_ready, check_stack_in_progress
from integration_tests.core.stack.queries import update_stack


def set_env_params(client, env, **new_params):
    old_params = {param.key: param.value for param in env.parameters}
    updated_params = {**old_params, **new_params}

    # update env only if there are param updates
    if old_params != updated_params:
        new_params_list = [{'key': param[0], 'value': param[1]} for param in updated_params.items()]
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
