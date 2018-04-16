

from timelaps.Delivery import DeliveryBoy
from paramiko import SSHClient

class SendImageRmq(DeliveryBoy):

    def is_free_to_send(self):
        return True

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
