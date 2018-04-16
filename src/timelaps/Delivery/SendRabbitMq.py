"""
 send source file via RMQ

"""
from statsd.defaults.django import statsd
from time import time
import socket
from django.conf import settings
import pika
from timelaps.Delivery.DeliveryBoy import DeliveryBoy

from logging import getLogger

logger = getLogger("timelaps.Delivery")


class SendImageRmq(DeliveryBoy):
    def is_free_to_send(self):
        is_ok = False
        conn = pika.URLParameters(settings.TIMELAPS_RMQ_BROKER)
        connection = pika.BlockingConnection(conn)
        channel = connection.channel()
        ex = channel.exchange_declare(settings.TIMELAPS_RMQ_EXCHANGE_NAME,
                                      settings.TIMELAPS_RMQ_EXCHANGE_TYPE)

        q = channel.queue_declare(queue=settings.TIMELAPS_RMQ_QUEUE, durable=True,
                                  arguments={'x-message-ttl': settings.TIMELAPS_RMQ_QUEUE_TIMEOUT})
        channel.queue_bind(settings.TIMELAPS_RMQ_QUEUE, settings.TIMELAPS_RMQ_EXCHANGE_NAME, "image")
        q_len = q.method.message_count
        statsd.gauge("timelaps.unprocessed_images", q_len)
        if q_len < settings.TIMELAPS_MAX_IMAGES_IN_QEUE:
            is_ok = True
        else:
            logger.error("Too many messages in queue")
        return is_ok

    def send_file(self, f_name, x_type='timelaps'):
        f = open(f_name, "rb")
        i = f.read()
        conn = pika.URLParameters(settings.TIMELAPS_RMQ_BROKER)
        connection = pika.BlockingConnection(conn)
        channel = connection.channel()

        ex = channel.exchange_declare(settings.TIMELAPS_RMQ_EXCHANGE_NAME,
                                      settings.TIMELAPS_RMQ_EXCHANGE_TYPE)

        q = channel.queue_declare(queue=settings.TIMELAPS_RMQ_QUEUE, durable=True,
                                  arguments={'x-message-ttl': settings.TIMELAPS_RMQ_QUEUE_TIMEOUT})
        channel.queue_bind(settings.TIMELAPS_RMQ_QUEUE, settings.TIMELAPS_RMQ_EXCHANGE_NAME, "image")

        bp = pika.spec.BasicProperties(timestamp=time(), cluster_id=socket.gethostname(),
                                       headers={'x-file-name': f_name, 'x-type': x_type})
        channel.basic_publish(exchange=settings.TIMELAPS_RMQ_EXCHANGE_NAME, routing_key="image", body=i, properties=bp)
        connection.close()
