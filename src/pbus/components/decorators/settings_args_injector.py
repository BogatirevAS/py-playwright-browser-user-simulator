import inspect
import logging
import weakref
from functools import wraps
from typing import Optional, Dict, List

from logger import ValidateMixin, Decoratable


class PbusSettingsArgsInjector(ValidateMixin):
    def __init__(self, args_dict: Optional[Dict[str, str]] = None, args_list: Optional[List[str]] = None,
                 method_name: Optional[str] = None, prefix="", validate=True):
        super().__init__(validate)
        self.args_dict = args_dict or {}
        self.args_list = args_list or []
        self._method_name = method_name
        self.prefix = prefix
        self._method_validated = False
        self._cached_settings_kwargs = weakref.WeakKeyDictionary()
        self.func: Optional[Decoratable] = None
        self._method_args: Optional[list] = None
        self._has_kwargs = None

    @property
    def method_name(self) -> str:
        if not self._method_name:
            self._method_name = self.func.__name__
        return self._method_name

    @property
    def method_args(self):
        if not self._method_args:
            sig = inspect.signature(self.func)
            # Exclude self
            self._method_args = list(sig.parameters.keys())[1:]
        return self._method_args

    @property
    def has_kwargs(self):
        if self._has_kwargs is None:
            sig = inspect.signature(self.func)
            self._has_kwargs = False
            for param in sig.parameters.values():
                if param.kind == param.VAR_KEYWORD:
                    self._has_kwargs = True
                    break
        return self._has_kwargs

    def __call__(self, func: Decoratable) -> Decoratable:
        if not self.func:
            self.func = func
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(impl, *args, **kwargs):
                self.logger.debug(f'Async decorator for "{func.__name__}"')
                kwargs = self._execute(impl, *args, **kwargs)
                return await func(impl, *args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(impl, *args, **kwargs):
                self.logger.debug(f'Sync decorator for "{func.__name__}"')
                kwargs = self._execute(impl, *args, **kwargs)
                return func(impl, *args, **kwargs)
            return sync_wrapper

    def _execute(self, impl, *args, **kwargs):
        self.logger.debug(f"Input kwargs: {kwargs}")
        if not hasattr(impl, 'settings'):
            self.validate_msg(f'No "settings" in {impl.__class__.__name__}')
        else:
            self._validate_method_signature_once()

            cached_kwargs = self._get_cached_settings_kwargs(impl)
            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.debug(f"All cached kwargs: {dict(self._cached_settings_kwargs)}")

            kwargs = self._update_kwargs(kwargs, cached_kwargs)
            self.logger.debug(f"Output kwargs: {kwargs}")
        return kwargs

    def _validate_method_signature_once(self):
        if not self._method_validated:
            self._validate_method_signature()
            self._method_validated = True

    def _validate_method_signature(self):
        """Validate that injected arguments exist in method signature"""
        self.logger.debug(f"Method args: {self.method_args}")
        # Ordered set
        injected_args = list(dict.fromkeys(list(self.args_dict.keys()) + self.args_list))
        self.logger.debug(f"Injected args: {injected_args}")

        if not self.has_kwargs:
            error_args = []
            for arg in injected_args:
                if arg not in self.method_args:
                    error_args.append(arg)
            if error_args:
                self.validate_msg(f"Arguments {error_args} not found in "
                                  f"'{self.func.__name__}' signature {self.method_args}")

    def _get_cached_settings_kwargs(self, impl):
        if impl not in self._cached_settings_kwargs:
            self._cache_settings_kwargs(impl)
        return self._cached_settings_kwargs[impl]

    def _cache_settings_kwargs(self, impl):
        settings = getattr(impl, 'settings')
        temp_args = self.args_dict.copy()

        if self.args_list:
            for arg in self.args_list:
                setting = f"{self.method_name}_{arg}"
                if arg in temp_args:
                    msg = f"Arguments conflict: '{arg}' already mapped in {temp_args}"
                    if temp_args[arg] != setting:
                        msg = f"{msg} with other {setting}"
                    self.validate_msg(msg)
                temp_args[arg] = setting

        if self.prefix:
            temp_args = {arg: f"{self.prefix}{setting}" for arg, setting in temp_args.items()}

        kwargs = {}
        error_settings = []
        for arg, setting in temp_args.items():
            if hasattr(settings, setting):
                kwargs[arg] = getattr(settings, setting)
            else:
                error_settings.append(setting)
        if error_settings:
            self.validate_msg(f"No settings arguments: {error_settings}")

        if not self.has_kwargs and not self.validate:
            kwargs = self._filter_kwargs_by_method_args(kwargs)

        self._cached_settings_kwargs[impl] = kwargs
        self.logger.debug(f"Cached kwargs: {kwargs}")

    def _filter_kwargs_by_method_args(self, kwargs: Dict[str, str]) -> Dict[str, str]:
        self.logger.debug(f"Before filtration: {kwargs}")
        return {k: v for k, v in kwargs.items() if k in self.method_args}

    @staticmethod
    def _update_kwargs(kwargs, cached_kwargs) -> Dict[str, str]:
        for key, value in cached_kwargs.items():
            if kwargs.get(key, None) is None:
                kwargs[key] = value
        return kwargs
