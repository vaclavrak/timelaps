from logging import getLogger
from timelaps.models import make_picture, send_picture, panorama_image
from celery import shared_task
from django.conf import settings
from timelaps.rotator import Rotator
from serial import Serial
logger = getLogger("webapp.timelapscam")


@shared_task
def make_image_from_camera():
    logger.info("Scheduled `make_image_from_camera`")
    if make_picture(settings.GPHOTO_IMAGE):
        send_picture(settings.GPHOTO_IMAGE)
    if settings.ROTATOR:
        logger.info("Going to rotate")
        r = Rotator(settings.ROTATOR_SERIAL_COM, settings.ROTATOR_SERIAL_SPEED)
        r.rotate(settings.ROTATOR_STEP)


@shared_task
def make_panorama_image():
    if settings.ROTATOR is not True:
        raise RuntimeError("No rotatory, can't make panorama")
    logger.info("Scheduled `make_panorama_image`")

    ser = Serial(settings.ROTATOR_SERIAL_COM, settings.ROTATOR_SERIAL_SPEED)

    panorama_image(settings.ROTATOR_PANORAMA_IMAGE, ser, settings.ROTATOR_PANORAMA_START, settings.ROTATOR_PANORAMA_STOP,
                  settings.ROTATOR_PANORAMA_ITER, settings.ROTATOR_PANORAMA_SLEEP)


