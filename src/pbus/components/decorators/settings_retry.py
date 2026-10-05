import inspect
from functools import wraps
from typing import Optional

from logger import ValidateMixin, Decoratable


class PbusSettingsRetry(ValidateMixin):
    def __init__(self, retries: Optional[int] = None, validate=True, settings_name="settings", setting_key="retries"):
        super().__init__(validate)
        self.retries = retries
        self.settings_name = settings_name
        self.setting_key = setting_key

    def __call__(self, func: Decoratable) -> Decoratable:
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(impl, *args, **kwargs):
                self.logger.debug(f'Async decorator for "{func.__name__}"')
                return await self._async_execute(func, impl, *args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(impl, *args, **kwargs):
                self.logger.debug(f'Sync decorator for "{func.__name__}"')
                return self._sync_execute(func, impl, *args, **kwargs)
            return sync_wrapper

    def _get_retries(self, impl):
        if self.retries is not None:
            return self.retries
        if not hasattr(impl, self.settings_name):
            self.validate_msg(f'No settings "{self.settings_name}" in {impl.__class__.__name__}')
            return None
        settings = getattr(impl, self.settings_name)
        if not hasattr(settings, self.setting_key):
            self.validate_msg(f'No settings key "{self.setting_key}" in {settings.__class__.__name__}')
            return None
        self.retries = getattr(settings, self.setting_key)
        return self.retries

    async def _async_execute(self, func: Decoratable, impl, *args, **kwargs):
        retries = self._get_retries(impl)
        if retries is None:
            return await func(impl, *args, **kwargs)

        self.logger.debug(f"{impl.__class__.__name__}.{func.__name__}(), retries = {retries}")

        for i in range(retries + 1):
            try:
                return await func(impl, *args, **kwargs)
            except Exception as e:
                if i == retries:
                    raise e
                self.logger.warning(f"{e}, retry {i + 1}")

    def _sync_execute(self, func: Decoratable, impl, *args, **kwargs):
        retries = self._get_retries(impl)
        if retries is None:
            return func(impl, *args, **kwargs)

        self.logger.debug(f"{impl.__class__.__name__}.{func.__name__}(), retries = {retries}")

        for i in range(retries + 1):
            try:
                return func(impl, *args, **kwargs)
            except Exception as e:
                if i == retries:
                    raise e
                self.logger.warning(f"{e}, retry {i + 1}")
