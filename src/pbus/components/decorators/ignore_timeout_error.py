import inspect
from functools import wraps

from logger import LoggerMixin, Decoratable
from pbus.components.exceptions import PlaywrightTimeoutError


class IgnoreTimeoutError(LoggerMixin):
    def __call__(self, func: Decoratable) -> Decoratable:
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(impl, *args, **kwargs):
                self.logger.debug(f'Async decorator for "{func.__name__}"')
                try:
                    return await func(impl, *args, **kwargs)
                except PlaywrightTimeoutError:
                    self.logger.warning(f"Ignore timeout error: {impl.__class__.__name__}.{func.__name__}()")
                    return None
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(impl, *args, **kwargs):
                self.logger.debug(f'Sync decorator for "{func.__name__}"')
                try:
                    return func(impl, *args, **kwargs)
                except PlaywrightTimeoutError:
                    self.logger.warning(f"Ignore timeout error: {impl.__class__.__name__}.{func.__name__}()")
                    return None
            return sync_wrapper
