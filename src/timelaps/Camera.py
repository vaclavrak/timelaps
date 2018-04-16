"""

  basic service wrapper for making picture


"""
from django.core.cache import cache
from django.conf import settings
from time import sleep, time
from timelaps.gPhotoWrapper import gPhotoWrapper
import gphoto2 as gp
import subprocess
from logging import getLogger
import redis
from socket  import gethostname
from serial import Serial
from timelaps.Controller import  Configurator
from timelaps.LogData import BasicLogData
logger = getLogger("core")


class CameraError(Exception):
    pass


class Camera(object):
    _serial = None
    _redis = None
    _config = None
    _bl  = None
    _cameras = None

    def __init__(self):
        self._serial = None
        self._redis = None
        self._config = None
        self._bl = None

    def set_serial(self, ser : Serial) -> object:
        self._serial = ser
        return self

    def set_redis(self, red : redis.StrictRedis) -> object:
        self._redis = red
        return self

    def set_config(self, cfg: Configurator):
        if not isinstance(cfg, Configurator):
            raise CameraError("Invalid config type")
        self._config = cfg
        return self

    def set_logger(self, bl: BasicLogData) -> object:
        self._bl = bl
        return self


    @property
    def log(self) -> BasicLogData:
        if self._bl is None:
            raise CameraError("Basic logger is not set, call set_logger first.")
        return self._bl

    @property
    def config(self) -> Configurator:
        if self._config is None:
            raise CameraError("Config is not set, call set_config first.")
        return self._config


    @property
    def serial(self):
        if self._serial is None:
            raise CameraError("no serial class specified, call set_serial first")
        if not self._serial.isOpen():
            self._serial.open()
        return self._serial

    @property
    def redis(self):
        if self._redis is None:
            raise CameraError("no redis class specified, call set_redis first")
        return self._redis

    def _serial_close(self):
        self.serial.close()
        # self._serial = None

    @property
    def is_on_battery(self):
        rps = self.config.get_kv("redis_power_state_rpi", "{hostname}:mini_ups:voltage:power_state")
        rps = rps.format(hostname=gethostname())
        return float(self.redis.get(rps, 0)) == 0.0

    @property
    def is_power_ok(self):
        cps = self.config.get_kv("redis_power_state_camera", "{hostname}:mini_ups:power_state:camera")
        cps = cps.format(hostname=gethostname())

        pok = self.config.get_kv("redis_power_state_picture_ok", "{hostname}:mini_ups:voltage:make_picture_ok")
        pok = pok.format(hostname=gethostname())

        if float(self.redis.get(cps)) == 0.0 and self.redis.get(pok) == "0":
            return False
        return True

    @property
    def light(self):
        k = self.config.get_kv("redis_light_key", "{hostname}:light:min")
        k = k.format(hostname=gethostname())
        return float(self.redis.get(k))

    def set_camera_power(self, state):
        if state is True:
            self.serial.write(bytes('1/2/', 'utf-8'))
        if state is False:
            self.serial.write(bytes('1/3/', 'utf-8'))
        self._serial_close()

    @property
    def find_camera(self):
        context = gp.gp_context_new()
        port_info_list = gp.check_result(gp.gp_port_info_list_new())
        gp.check_result(gp.gp_port_info_list_load(port_info_list))
        abilities_list = gp.check_result(gp.gp_abilities_list_new())
        gp.check_result(gp.gp_abilities_list_load(abilities_list, context))
        self._cameras = gp.check_result(gp.gp_abilities_list_detect(abilities_list, port_info_list, context))
        found_device = False
        for name, value in self._cameras:
            logger.debug("%s, %s" % (name, value))
            found_device = True

        return found_device

    @property
    def init_camera(self):
        found_device = self.find_camera
        if found_device is False:
            self.set_camera_power(False)
            sleep(3)
            self.set_camera_power(True)
            sleep(3)
            found_device = self.find_camera
        return found_device

    def make_photo(self, f_name, light):
        gpw = gPhotoWrapper(light, filename=f_name).set_logger(self.log)
        lsl = float(self.config.get_kv("light_shadow_limit"))
        lnl = float(self.config.get_kv("light_night_limit"))

        gpw.optimize(shadow_threshold=lsl, night_threshold=lnl)

        c = " ".join(gpw.command)
        logger.info(c)

        child = subprocess.Popen(c, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        (standard_out, junk) = child.communicate()

        if standard_out is not None:
            logger.debug(standard_out)
        if junk is not None:
            logger.error(junk)

