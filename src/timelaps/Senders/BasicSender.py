
from abc import abstractmethod
from locale import str
from time import time
import socket
from timelaps.Controller import Configurator


class SenderException(Exception):
    pass


class DataListException(Exception):
    pass


class DataItem(object):
    _data = None
    _prefix = None

    def __init__(self, d: dict, k: str):
        self._data = d
        self.prefix = k

    @property
    def key_list(self):
        k = [self.prefix]
        for dk in self._data.get("key", []):
            k.append(dk)
        return k

    @property
    def value(self):
        return self._data.get("value", None)

    @property
    def original_metric(self):
        return self._data.get("original_key", None)


class DataList(object):
    _data = []
    _global_prefix = None

    def __init__(self):
        self._data = []
        self._global_prefix = None

    def append(self, data):
        self._data.append(DataItem(data, self.prefix))
        return self

    @property
    def pop_item(self) -> DataItem:
        if len(self._data) == 0:
            return None
        return self._data.pop(0)

    def set_global_prefix(self, prefix):
        self._global_prefix = prefix
        return self

    @property
    def prefix(self):
        if self._global_prefix is None:
            raise DataListException("No prefix defined")
        return self._global_prefix


class Sender(object):
    _data = None
    _prefix = None
    _config = None

    def __init__(self):
        self._data = None
        self._prefix = None
        self._config = None

    @property
    def name(self) -> str:
        return self.__module__.split(".")[-1]

    @property
    def hostname(self) -> str:
        pref = socket.gethostname()
        pref = pref.split(".")
        return pref[-1]

    @property
    def prefix(self):
        if self._prefix is None:
            self._prefix = self.config.get_kv("global_prefix", self.hostname)

        return self._prefix

    @property
    def data(self) -> DataList:
        if self._data is None:
            self._data = DataList()
            self._data.set_global_prefix(self.prefix)
        return self._data

    def send_data(self, key: list, val: float, original_key: str) -> object:
        self.data.append({'key': key, 'value': val, 'original_key': original_key, 'data_received': time()})
        return self

    @abstractmethod
    def flush(self, cnf:dict) -> object:
        pass

    @abstractmethod
    def setup(self) -> object:
        return self

    def set_config(self, cfg: Configurator):
        if not isinstance(cfg, Configurator):
            raise SenderException("Invalid config type")
        self._config = cfg
        return self

    @property
    def config(self) -> Configurator:
        return self._config


class SenderList(object):
    _senders = {}
    _configs = {}

    def __init__(self):
        self._senders = {}
        self._configs = {}

    def append(self, name: str, sender_provider: Sender, kwargs: dict = None)-> object:
        self._senders[name] = sender_provider
        self._configs[name] = kwargs

        return self

    def get_by_name(self, name: str) -> (Sender, dict):
        return (self._senders.get(name, None), self._configs.get(name, {}))

    def __iter__(self):
        for s in self._senders:
            yield s

    def send_data(self, key:list, value:str, origin_code: str) -> object:
        for s in self._senders:
            self._senders[s].send_data(key, value, origin_code)
        return self

    def flush(self):
        for s in self._senders:
            self._senders[s].flush(self._configs[s])
        return self
