

from timelaps.Senders.BasicSender import Sender
import redis


class RedisSenderException(Exception):
    pass


class RedisSender(Sender):
    _redis = None
    _host = None
    _db  = None
    _port = None

    @property
    def redis(self) -> redis.StrictRedis:
        if self._redis is None:
            self._redis = redis.StrictRedis(host=self._host, port=self._port, db=self._db)
        return self._redis

    def flush(self, cnf:dict) -> object:
        pipe = self.redis.pipeline()
        while True:
            d = self.data.pop_item
            if d is None:
                break
            current_key = ":".join(d.key_list)
            pipe.set(current_key, d.value)
            # self.redis.set(current_key, d.value)
        pipe.execute()
        return self

    def setup(self) -> object:
        self._host = self.config.get_kv("data_resorces/redis/host", "localhost")
        self._port = self.config.get_kv("data_resorces/redis/port", 6379)
        self._db = self.config.get_kv("data_resorces/redis/database", 0)
        return self