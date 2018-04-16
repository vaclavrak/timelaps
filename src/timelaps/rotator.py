"""

  camera rotator control

"""

from serial import Serial
from logging import getLogger
from webcam.signals import *

logger = getLogger("webapp.timelapscam")


class Rotator(object):
    _port = ""
    _speed = 0
    _serial = None
    c = {"20": rot_temp, "21": rot_step_counter, "22": rot_magnetometer, "23": rot_turnover_step, "24": rot_start_point,
         "25": rot_calibration, "26": rot_direction}

    def __init__(self, serial_port, serial_speed):
        self._serial = None
        self._port = serial_port
        self._speed = serial_speed

    @property
    def serial(self):
        if self._serial is None:
            self._serial = Serial(self._port, self._speed, timeout=1)
        if not self._serial.isOpen():
            self._serial.open()
        return self._serial

    def _serial_close(self):
        self.serial.close()
        self._serial = None

    def rotate(self, step = 1):
        logger.info("Rotate step %d" % step)
        self.serial.write('2/8/%d/' % step)
        codes = []
        for i in range(0,7):
            ln = self.serial.readline()
            ln = ln.strip()
            if ln:
                self.process_codes(ln)

        self._serial.close()

    def process_codes(self, ln):
        try:
            a = ln.split("/")
            if len(a) >= 3:
                dev, code, value = a[0:3]
                value = float(value)
                self.c[code].send(sender=self.__class__, value_list=[value])

        except ValueError as e:
            logger.error("Error processing line `%s`, error %s" % (ln, e))

