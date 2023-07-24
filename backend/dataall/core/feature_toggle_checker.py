"""
Contains decorators that check if a feature has been enabled or not
"""
from dataall.base.config import config
from dataall.base.utils.decorator_utls import process_func


def is_feature_enabled(config_property: str):
    def decorator(f):
        fn, fn_decorator = process_func(f)

        def decorated(*args, **kwargs):
            value = config.get_property(config_property)
            if not value:
                raise Exception(f"Disabled by config {config_property}")
            return fn(*args, **kwargs)

        return fn_decorator(decorated)
    return decorator
