"""
Contains decorators that check if a feature has been enabled or not
"""

import functools
from typing import List, Any, Optional, Callable

from dataall.base.config import config
from dataall.base.utils.decorator_utls import process_func


def is_feature_enabled(config_property: str):
    def decorator(f):
        fn, fn_decorator = process_func(f)

        @functools.wraps(fn)
        def decorated(*args, **kwargs):
            value = config.get_property(config_property)
            if not value:
                raise Exception(f'Disabled by config {config_property}')
            return fn(*args, **kwargs)

        return fn_decorator(decorated)

    return decorator


def is_feature_enabled_for_allowed_values(
    allowed_values: List[Any],
    enabled_values: List[Any],
    default_value: Any,
    resolve_property: Optional[Callable] = None,
    config_property: Optional[str] = None,
):
    def decorator(f):
        fn, fn_decorator = process_func(f)

        @functools.wraps(fn)
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
            if value not in enabled_values:
                raise Exception(f'Disabled by config: {value}. Enable config value(s): {", ".join(enabled_values)}')
            return fn(*args, **kwargs)

        return fn_decorator(decorated)

    return decorator
