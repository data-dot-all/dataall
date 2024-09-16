from functools import wraps
from dataall.base.config import config
from dataall.base.context import get_context


def is_stack_logs_visible():
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwds):
            print(get_context().groups)
            target_type = kwds['targetType']
            if not target_type:
                raise Exception('target_type is missing when calling decorator "is_stack_logs_visible"')
            value = 'disabled'
            if target_type == 'environment':
                value = config.get_property('core.features.show_stack_logs')
            if target_type == 'dataset':
                value = config.get_property('modules.s3_datasets.features.show_stack_logs')
            if target_type == 'shares':
                value = config.get_property('modules.s3_datasets_shares.features.show_stack_logs')

            if value == 'enabled':
                return f(*args, **kwds)
            if value == 'admin-only':
                return (
                    f(*args, **kwds)
                    if 'DAAdministrators' in get_context().groups
                    else Exception('Stack logs are only visible to data.all administrators')
                )

            raise Exception('Stack logs are disabled. Please check "show_stack_logs" config in config.json')

        return wrapper

    return decorator
