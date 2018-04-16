

from timelaps.Senders.BasicSender import Sender
import time
import calendar

import socket
from logging import getLogger

logger = getLogger("core")


class CarbonSenderException(Exception):
    pass


class myCarbonClient(object):
    _vals = []
    _client = None
    _ip = None
    _port = None

    def __init__(self):
        self._vals = []
        self._client = None

    def set_addres(self, ip, port):
        self._ip = ip
        self._port = port
        return self

    def add(self, name:str, value:str) -> object:

        ts = calendar.timegm(time.gmtime())

        s = "{dim} {val} {ts}".format(dim=name, val=value, ts=ts )
        self._vals.append(s)
        return self

    @property
    def client(self):
        if self._client is None:
            self._client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._client.connect((self._ip, self._port))
        return self._client

    def close(self):
        if self._client is not None:
            self.client.close()
        self._client = None
        return self

    def send(self):
        try:
            self.client.send(bytes("\n".join(self._vals), 'utf-8'))
            self.close()
        except TimeoutError as e:
            logger(e)

        return self


class CarbonSender(Sender):
    _host = None
    _port = None
    _cc = None
    _except_metrics = []

    def __init__(self):
        self._host = None
        self._port = None
        self._cc = None
        self._except_metrics = []

    @property
    def carbon(self) -> myCarbonClient:
        if self._cc is None:
            self._cc = myCarbonClient().set_addres(self._host, self._port)
        return self._cc

    def flush(self, cnf:dict) -> object:
        while True:
            d = self.data.pop_item

            if d is None:
                break
            if d.original_metric in cnf.get('except', []):
                continue
            tk = ".".join(d.key_list)
            tk = tk.replace("-", "_")
            self.carbon.add(tk,d.value)
        self.carbon.send()

    def setup(self) -> object:
        self._host = self.config.get_kv("data_resorces/carbon/host", "localhost")
        self._port = self.config.get_kv("data_resorces/carbon/port", 2003)
        return self