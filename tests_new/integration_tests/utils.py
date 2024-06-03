import logging
import time
from functools import wraps
from typing import Callable, Optional

log = logging.getLogger(__name__)


def poller(
    check_success: Callable,
    timeout: Optional[float] = float('inf'),
    sleep_time: Optional[float] = 10.0,
):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            current_timeout = timeout
            while not check_success(retval := function(*args, **kwargs)):
                log.debug(f'polling {current_timeout} {retval}')
                time.sleep(sleep_time)
                current_timeout -= sleep_time
                if current_timeout <= 0:
                    raise TimeoutError('Timeout')
            return retval

        return wrapper

    return decorator
