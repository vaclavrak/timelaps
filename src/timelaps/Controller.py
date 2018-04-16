import os
import yaml
import sys
from logging import getLogger
import inotify.adapters
import threading

logger = getLogger("core")


class ConfiguratorException(Exception):
    pass


class Configurator(object):
    _src = None
    _yml = None
    _context = {}
    _i = None
    _wt = None

    def __init__(self):
        self._src = None
        self._yml = None
        self._context = {}
        self._i = None
        self._wt = None

    def get_kv(self, slash_key, def_val = None):
        keys = slash_key.split("/")
        keys.reverse()
        result = self._config
        while len(keys) > 0:
            if result is None:
                break
            k = keys.pop()
            result = result.get(k, (def_val if len(keys) == 0 else {}))
        return result

    def get_kvs(self, slash_key, def_val = None):
        try:
            keys = slash_key.split("/")
            keys.reverse()
            result = self._config
            while len(keys) > 0:
                if result is None:
                    break
                if isinstance(result, list):
                    result = None
                    break
                result = result.get(keys.pop(), (def_val if len(keys) == 1 else {}))
            if result is not None:
                if isinstance(result, list):
                    for ln in result:
                        yield ln
                else:
                    k = list(result.keys())
                    k.reverse()
                    for i_k in k:
                        yield i_k

        except Exception as e:
            logger.exception(e)
            raise e
        return None

    def make_context(self):
        for cx in self.get_kvs('context'):
            __import__("carve.context.{cls}".format(cls=cx))
            src_module = sys.modules["carve.context.{cls}".format(cls=cx)]
            src_class = getattr(src_module, cx)
            contextor = src_class().set_config(self)
            for nm in self.get_kvs('context/{}'.format(cx)):
                contextor.set_prefix("context/{}/{}".format(cx, nm))
                contextor.prepare_context()

    @property
    def sources(self):
        for s in self.get_kvs('source'):
            __import__("carve.sources.{cls}".format(cls=s))
            src_module = sys.modules["carve.sources.{cls}".format(cls=s)]
            src_class = getattr(src_module, s)
            yield src_class().set_config(self)

    def watch_config_change(self):
        self._i = inotify.adapters.Inotify()
        self._i.add_watch(os.path.dirname(self._src))
        for event in self._i.event_gen():
            if event is None:
                continue
            (header, type_names, watch_path, filename) = event
            if filename != os.path.basename(self._src):
                continue
            should_be_reloaded = False
            for tp in ['IN_MOVED_FROM', 'IN_CLOSE_WRITE']:
                if tp in type_names:
                    should_be_reloaded = True
            if should_be_reloaded is False:
                continue
            logger.info("Config changed {}".format(self._src))
            self._yml = None
        return self

    @property
    def _config(self) -> dict:
        if self._yml is None:
            if self._src is None:
                raise ConfiguratorException("No config file defined, call read(f_name) first.")

            with open(self._src, "r") as f:
                self._yml = yaml.load(f)
            if self._wt is None:
                self._wt = threading.Thread(target=self.watch_config_change)
                self._wt.start()

        return self._yml

    def read(self, f_name):
        self._src = f_name
        return self

    def set_context(self, k : str, v : str) -> object:
        self._context[k] = v
        return self

    @property
    def context(self) -> dict:
        return self._context
