

from timelaps.Senders.BasicSender import Sender
from copy import copy

class FileSenderException(Exception):
    pass


class FileSender(Sender):

    def flush(self, cnf:dict) -> object:
        f_name = cnf.get('fileName')
        while True:
            d = self.data.pop_item
            if d is None:
                break
            vars = {
                'last_key': copy(d.key_list[-1]),
                'key': "_".join(d.key_list)
            }
            temp_name = f_name.format(**vars)
            with open(temp_name, 'w') as f:
                f.write(str(d.value))

    def setup(self) -> object:
        return self