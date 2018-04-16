"""

 Camera version 2
 ==================

 by Vena

 make picture and store it in Rmq or filesystem


"""


from django.core.management.base import BaseCommand
from django.conf import settings
from timelaps.models import make_picture, send_picture
from timelaps.Controller import  Configurator
from timelaps.LogData import BasicLogData
from timelaps.Camera import Camera
from serial import Serial
import redis


class Command(BaseCommand):
    help = 'make picture from camera'
    image_archive = None

    def add_arguments(self, parser):
        parser.add_argument('--cnf', '-c', dest='config',  default="/etc/webcam/make-picture.yml",
                            help='config file default is /etc/webcam/make-picture.yml')

    def __init__(self):
        super(Command, self).__init__()

    def handle(self, *args, **options):
        conf = options['config']
        config = Configurator().read(conf)
        bl = BasicLogData().set_config(config)

        serial_com = config.get_kv("serial/device")
        serial_speed = config.get_kv("serial/speed", 9600)

        ser = Serial(serial_com, serial_speed)

        red_host = config.get_kv("data_resorces/redis/host", "localhost")
        red_port = config.get_kv("data_resorces/redis/port", 6379)
        red_db = config.get_kv("data_resorces/redis/database", 0)

        r = redis.StrictRedis(host=red_host, port=red_port, db=red_db)

        cam = Camera()
        cam.set_serial(ser).set_redis(r)
        make_picture(config, bl, cam)
        # if make_picture(config, bl, cam):
        #     send_picture(config, bl)