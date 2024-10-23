from dataall.core.resource_threshold.db.resource_threshold_repositories import ResourceThresholdRepository
from dataall.base.db import exceptions
from functools import wraps

import logging

log = logging.getLogger(__name__)


class ResourceThresholdService:
    @staticmethod
    def check_invocation_count(action_type, max_count_config_path):
        def decorator(func):
            @wraps(func)
            def wrapper(session, username, *args, **kwargs):
                count = ResourceThresholdRepository.get_count_today(
                    session=session, username=username, action_type=action_type
                )
                max_count = config.get_property(max_count_config_path, 10)
                log.info(f'User {username} has invoked {action_type} {count} times today of max {max_count}')
                if count < max_count:
                    if count == 0:
                        ResourceThresholdRepository.add_entry(
                            session=session, username=username, action_type=action_type
                        )
                    else:
                        ResourceThresholdRepository.increment_count(
                            session=session, username=username, action_type=action_type
                        )
                    return func(session, username, *args, **kwargs)
                else:
                    raise exceptions.ResourceThresholdExceeded(username=username, action=action_type)

            return wrapper

        return decorator
