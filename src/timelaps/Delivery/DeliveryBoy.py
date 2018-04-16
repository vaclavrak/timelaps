
import abc

class DeliveryBoy(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def is_free_to_send(self):
        pass

    @abc.abstractmethod
    def send_file(self):
        pass