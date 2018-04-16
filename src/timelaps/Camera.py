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

logger = getLogger("webapp.timelapscam")


class CameraError(Exception):
    pass


class Camera(object):
    _serial = None
    _redis = None
    _config = None
    # gPhoto2 camera list
    _cameras = None

    def __init__(self):
        self._serial = None
        self._redis = None
        self._config = None

    def set_serial(self, ser : Serial) -> object:
        self._serial = ser
        return self

    def set_redis(self, red : redis.StrictRedis) -> object:
        self._serial = red
        return self

    def set_config(self, cfg: Configurator):
        if not isinstance(cfg, Configurator):
            raise CameraError("Invalid config type")
        self._config = cfg
        return self

    @property
    def config(self) -> Configurator:
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
        self._serial = None

    @property
    def is_on_battery(self):
        return cache.get("power-state", False) == 0

    @property
    def is_power_ok(self):
        k = self.config.get_kv("redis_light_key", "{hostname}.light.min")

        if cache.get("power-state", 0) == 0 and cache.get("power-state-picture-ok", 0) == 0:
            return False
        return True

    @property
    def light(self):
        k = self.config.get_kv("redis_light_key", "{hostname}.light.min")
        k = k.format(hostname=gethostname())
        return redis.get(k, 0)

    def set_camera_power(self, state):
        if state is True:
            self.serial.write('1/2/')
        if state is False:
            self.serial.write('1/3/')
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
        gpw = gPhotoWrapper(light, filename=f_name)
        gpw.optimize(shadow_threshold=settings.LIGHT_SHADOW_THRESHOLD, night_threshold=settings.LIGHT_NIGHT_THRESHOLD)

        c = " ".join(gpw.command)
        logger.info(c)

        child = subprocess.Popen(c, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        (standard_out, junk) = child.communicate()

        if standard_out is not None:
            logger.debug(standard_out)
        if junk is not None:
            logger.error(junk)

