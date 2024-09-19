from typing import Optional, Callable, List, Any
from dataall.base.config import config
from dataall.base.utils.decorator_utls import process_func


def is_feature_has_allowed_values(
    allowed_values: List[Any],
    default_value: Any,
    resolve_property: Optional[Callable] = None,
    config_property: Optional[str] = None,
):
    def decorator(f):
        fn, fn_decorator = process_func(f)

        def decorated(*args, **kwargs):
            config_property_value = None
            if config_property is None and resolve_property is None:
                raise Exception('Config property not provided')
            if resolve_property:
                config_property_value = resolve_property(*args, **kwargs)
            if config_property:
                config_property_value = config_property
            value = config.get_property(config_property_value, default_value)
            if value not in allowed_values:
                raise Exception(
                    f'Disabled since incorrect values in config {config_property_value}. Correct config values {allowed_values}'
                )
            return fn(*args, **kwargs)

        return fn_decorator(decorated)

    return decorator
