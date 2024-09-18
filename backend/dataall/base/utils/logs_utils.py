from typing import Optional, Callable, List, Any
from dataall.base.config import config
from dataall.base.utils.decorator_utls import process_func


def is_feature_has_allowed_values(
    allowed_values: List[Any], resolve_property: Optional[Callable] = None, config_property: Optional[str] = None
) -> object:
    def decorator(f):
        fn, fn_decorator = process_func(f)

        def decorated(*args, **kwargs):
            config_property_value = None
            if config_property is None and resolve_property is None:
                raise Exception('Config property not provided')
            if resolve_property:
                config_property_value = resolve_property(*args, **kwargs)
            value = config.get_property(config_property_value)
            if value not in allowed_values:
                raise Exception(
                    f'Disabled since incorrect values in config {config_property_value}. Correct config values {allowed_values}'
                )
            return fn(*args, **kwargs)

        return fn_decorator(decorated)

    return decorator


def check_if_user_allowed_view_logs(groups, config):
    if (config == 'admin-only' and 'DAAdministrators' not in groups) or config == 'disabled':
        return False
    return True
