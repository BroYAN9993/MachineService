import pika
from contextlib import contextmanager

class RabbitHole:
    def __init__(self, host, exchange, exchange_type="fanout"):
        self.host = host
        self.exchange= exchange
        self.exchange_type = exchange_type
        self.connection = None
        self.rmq_channel = None

    def _get_or_create_channel(self):
        if self.rmq_channel:
            return self.rmq_channel
        else:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host))
            self.rmq_channel = self.connection.channel()
            self.rmq_channel.exchange_declare(exchange=self.exchange, exchange_type=self.exchange_type)
            return self.rmq_channel

    def publish(self, message):
        self._get_or_create_channel().basic_publish(exchange=self.exchange, routing_key='', body=message) 

    def get_consumer(self, callback):
        channel = self._get_or_create_channel()
        queue_name = channel.queue_declare(queue='', exclusive=True).method.queue
        channel.queue_bind(exchange=self.exchange, queue=queue_name)
        channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
        return channel

    def close(self):
        self.connection.close()

