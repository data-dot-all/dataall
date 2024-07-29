import re

from integration_tests.core.stack.queries import get_stack
from integration_tests.utils import poller


def is_stack_in_progress(stack):
    return re.match(r'.*IN_PROGRESS|PENDING', stack.status, re.IGNORECASE)


@poller(check_success=is_stack_in_progress, timeout=600)
def check_stack_in_progress(client, env_uri, stack_uri, target_uri=None, target_type='environment'):
    return get_stack(client, env_uri, stack_uri, target_uri or env_uri, target_type)


@poller(check_success=lambda stack: not is_stack_in_progress(stack), timeout=600)
def check_stack_ready(client, env_uri, stack_uri, target_uri=None, target_type='environment'):
    return get_stack(client, env_uri, stack_uri, target_uri or env_uri, target_type)


def wait_stack_delete_complete(cf_client, stack_name):
    # Wait for the stack to be deleted
    waiter = cf_client.get_waiter('stack_delete_complete')
    waiter.wait(
        StackName=stack_name,
        WaiterConfig={
            'Delay': 20,  # Delay between each poll request (in seconds)
            'MaxAttempts': 60,  # Maximum number of attempts before giving up
        },
    )
