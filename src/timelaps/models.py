import re
from datetime import datetime
from logging import getLogger
from timelaps.LogData import BasicLogData
from timelaps.Controller import  Configurator
import exifread

from timelaps.Camera import Camera

logger = getLogger("webapp.timelapscam")
bl = BasicLogData()

def _div(s):
    if s.find("/") == -1:
        return float(s)
    a, b = s.split("/")
    return float(a) / float(b)


def make_picture(config: Configurator, bl: BasicLogData, cam: Camera) -> bool:
    f_name = config.get_kv("basic_picture")

    t = datetime.now()
    # check energy
    if not cam.is_power_ok:
        logger.warning("Not enough power, camera is turning off")
        cam.set_camera_power(False)
        return False

    cam.set_camera_power(True)
    if cam.init_camera is False:
        logger.error("Cammera not found, turning camera power off")
        # cam.set_camera_power(False)
        return False

    light = cam.light
    if light is None:
        logger.error("Could not determine light, is dangerous to make picture")
        return False

    cam.make_photo(f_name, light)
    exif_log(config,bl)
    bl.add("camera.make_time", (datetime.now() - t).seconds)
    return True


def exif_log(config: Configurator, bl: BasicLogData):
    f_name = config.get_kv("basic_picture")

    f = open(f_name, 'rb')
    tags = exifread.process_file(f)
    data = {
        "camera.exif.ApertureValue": str(tags.get('EXIF ApertureValue', 'not-set')),
        "camera.exif.ExposureTime": _div(str(tags.get('EXIF ExposureTime', '0'))),
        "camera.exif.FocalLength": _div(str(tags.get('EXIF FocalLength', '0'))),
        "camera.exif.ShutterSpeedValue": _div(str(tags.get('EXIF ShutterSpeedValue', '0'))),
        "camera.exif.ShutterSpeedValue": _div(str(tags.get('EXIF ShutterSpeedValue', '0'))),
        "camera.exif.ISOSpeedRatings": str(tags.get('EXIF ISOSpeedRatings', 'not-set')),
        "camera.exif.FNumber": str(tags.get('EXIF FNumber', 'not-set')),
        "camera.exif.MeteringMode.%s" % str(tags.get('EXIF MeteringMode', 'not-set')): 1,
        "camera.exif.SceneCaptureType.%s" % str(tags.get('EXIF SceneCaptureType', 'not-set')): 1
    }

    for k in data:
        m = re.compile(r"([0-9]*)/([0-9]*)").match("%s" % data[k])
        if m:
            bl.add(k.split("."), float(m.group(1)) / float(m.group(2)))
        else:
            bl.add(k.split("."), data[k])
    bl.flush()
    f.close()
