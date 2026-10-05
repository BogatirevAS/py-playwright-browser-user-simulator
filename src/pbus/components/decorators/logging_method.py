import inspect
from functools import wraps

from logger import LogLevel, LoggerMixin, Decoratable


class LoggingMethod(LoggerMixin):
    def __init__(self, log_level: LogLevel = None):
        self._log_level = log_level

    def __call__(self, func: Decoratable) -> Decoratable:
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(impl, *args, **kwargs):
                self.logger.debug(f'Async decorator for "{func.__name__}"')
                self.impl_log(func, impl, *args, **kwargs)
                return await func(impl, *args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(impl, *args, **kwargs):
                self.logger.debug(f'Sync decorator for "{func.__name__}"')
                self.impl_log(func, impl, *args, **kwargs)
                return func(impl, *args, **kwargs)
            return sync_wrapper

    def impl_log(self, func: Decoratable, impl, *args, **kwargs):
        impl.logger.log(level=self.get_log_level(impl), msg=f"{func.__name__}, args={args}, kwargs={kwargs}")

    def get_log_level(self, impl):
        log_level = LogLevel.DEBUG
        if self._log_level is not None:
            log_level = self._log_level
        if hasattr(impl, "settings") and hasattr(impl.settings, "method_log_level"):
            log_level = impl.settings.method_log_level
        return log_level
