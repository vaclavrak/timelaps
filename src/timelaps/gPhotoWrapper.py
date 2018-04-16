__author__ = 'rak'


from logging import getLogger
from statsd.defaults.django import statsd

logger = getLogger("webapp.timelapscam")
td_logger = getLogger("camera.fluent")


class gPhotoWrapper(object):
    _light = None
    _shadow = None
    _capture = None
    _shooting_mode = None
    _iso = None
    _assist_light = None
    _white_balance = None
    _flash_mode = None
    _file_name = None
    _use_stdout = True # write to file via stdout redirect
    _capture_image_and_download = True
    _force_overwrite = True
    _shutter_speed = None

    def __init__(self, light, capture="on", shootingmode=0, iso=1, assistlight=0, whitebalance=0,
                 flashmode=4, filename="online.jpg", capture_image_and_download=True, force_overwrite=True,
                 shutterspeed=None):
        self._light = light
        self.capture(capture)
        self.shootingmode(shootingmode)
        self.iso(iso)
        self.assistlight(assistlight)
        self.whitebalance(whitebalance)
        self.flashmode(flashmode)
        self.filename(filename)
        self.capture_image_and_download(capture_image_and_download)
        self.force_overwrite(force_overwrite)
        self.shutter_speed(shutterspeed)

    def optimize(self, shadow_threshold=5, night_threshold=0):
        if self._light >= shadow_threshold:
            logger.info("It's day, light %d >= shadow %d " % (self._light, shadow_threshold))
            td_logger.info({"camera.gPhotoWrapper.day": 1, "camera.gPhotoWrapper.shadow": 0,
                            "camera.gPhotoWrapper.night": 0})
            statsd.gauge("camera.gPhotoWrapper.day", 1)
            statsd.gauge("camera.gPhotoWrapper.night", 0)
            statsd.gauge("camera.gPhotoWrapper.shadow", 0)
        elif self._light > night_threshold:
            logger.info("It's shadow, light %d >= night %d " % (self._light, night_threshold))
            td_logger.info({"camera.gPhotoWrapper.day": 0, "camera.gPhotoWrapper.shadow": 1,
                            "camera.gPhotoWrapper.night": 0})
            statsd.gauge("camera.gPhotoWrapper.day", 0)
            statsd.gauge("camera.gPhotoWrapper.night", 0)
            statsd.gauge("camera.gPhotoWrapper.shadow", 1)
            self.shootingmode(1)
            self.shutter_speed(6)
            self.whitebalance(None)
            self.flashmode(4)
            self.assistlight(1)
        else:
            td_logger.info({"camera.gPhotoWrapper.day": 0, "camera.gPhotoWrapper.shadow": 0,
                            "camera.gPhotoWrapper.night": 1})
            statsd.gauge("camera.gPhotoWrapper.day", 0)
            statsd.gauge("camera.gPhotoWrapper.night", 1)
            statsd.gauge("camera.gPhotoWrapper.shadow", 0)
            self.shootingmode(1)
            self.shutter_speed(0)
            self.whitebalance(None)
            self.flashmode(4) #
            self.assistlight(1)
            self.iso(0)

    @property
    def command(self):
        cmd = ['gphoto2',"--set-config capture=%s" % self._capture,
               "--set-config shootingmode=%s" % self._shooting_mode, "iso=%s" % self._iso,
               "--set-config assistlight=%s" % self._assist_light]
        if self._white_balance is not None:
            cmd.append("--set-config whitebalance=%s" % self._white_balance)
        cmd.append("--set-config flashmode=%s" % self._flash_mode)
        if self._shutter_speed is not None:
            cmd.append("--set-config shutterspeed=%s" % self._shutter_speed)
        if self._capture_image_and_download:
            cmd.append("--capture-image-and-download")
        if self._force_overwrite:
            cmd.append("--force-overwrite")

        # this rule have to be the last
        if self._file_name:
            if self._use_stdout is False:
                cmd.append("--filename %s" % self._file_name)
            else:
                cmd.append("--stdout > %s" % self._file_name)
        cmd = " ".join(cmd)
        cmd = cmd.split(" ")
        d = {
            "camera.gPhotoWrapper.light": self._light,
            "camera.gPhotoWrapper.capture": 1 if self._capture == 'on' else 0,
            "camera.gPhotoWrapper.shooting_mode": self._shooting_mode,
            "camera.gPhotoWrapper.iso": self._iso,
            "camera.gPhotoWrapper.assist_light": self._assist_light,
            "camera.gPhotoWrapper.white_balance": self._white_balance,
            "camera.gPhotoWrapper.flash_mode": self._flash_mode,
            "camera.gPhotoWrapper.shutter_speed": self._shutter_speed
        }
        td_logger.info(d)
        for k in d:
            if d[k] is None:
                continue
            statsd.gauge(k, d[k])
        return cmd

    def shutter_speed(self, v):
        self._shutter_speed = v
        return self

    def force_overwrite(self, b=True):
        self._force_overwrite = b
        return self

    def capture_image_and_download(self, b=True):
        self._capture_image_and_download = b
        return self

    def filename(self, fname, stdout = True):
        self._file_name = fname
        self._use_stdout = stdout
        return self

    def flashmode(self, v=4):
        self._flash_mode = v
        return self

    def whitebalance(self, v=1):
        self._white_balance = v
        return self

    def assistlight(self, v=0):
        self._assist_light = v
        return self

    def iso(self, v=1):
        self._iso = v
        return self

    def shootingmode(self, v=0):
        self._shooting_mode = v
        return self

    def capture(self, v="on"):
        self._capture = v
        return self