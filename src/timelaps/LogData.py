import sys
from timelaps.Controller import  Configurator


class BasicLogDataException(Exception):
    pass


class BasicLogData(object):
    _k = {}
    _v = {}
    _config = None

    def __init__(self):
        self._k = {}

    def add(self, m, v):
        kk = "_".join(m)
        self._k[kk] = m
        self._v[kk] = v
        return self

    def set_config(self, cfg: Configurator):
        if not isinstance(cfg, Configurator):
            raise BasicLogDataException("Invalid config type")
        self._config = cfg
        return self

    @property
    def config(self) -> Configurator:
        return self._config

    def flush(self):
        for sender in self.config.get_kvs('data_resorces'):
            sndr = sender.capitalize()
            __import__("timelaps.Senders.{cls}".format(cls=sndr))
            src_module = sys.modules["timelaps.Senders.{cls}".format(cls=sndr)]
            src_class = getattr(src_module, "{cls}Sender".format(cls=sndr))
            sender_cls = src_class().set_config(self.config).setup()
            for k in self._k.keys():
                sender_cls.send_data(self._k[k], self._v[k], k)
            sender_cls.flush({})
