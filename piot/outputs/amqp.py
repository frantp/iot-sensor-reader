import os

from ..core import DriverBase, format_msg
import pika


class Driver(DriverBase):
    def __init__(self, exchange, queue, routing_key=None, *args, **kwargs):
        super().__init__()
        self._args = args
        self._kwargs = kwargs
        self._exchange = exchange
        self._routing_key = routing_key or queue
        with pika.BlockingConnection(
             pika.ConnectionParameters(*self._args, **self._kwargs)) as c:
            channel = c.channel()
            channel.exchange_declare(exchange=exchange, durable=True)
            channel.queue_declare(queue=queue, durable=True)
            channel.queue_bind(
                exchange=exchange,
                queue=queue,
                routing_key=self._routing_key
            )

    def run(self, driver_id, ts, fields, tags):
        if not fields:
            return
        msg = format_msg(ts, driver_id, tags, fields)
        with pika.BlockingConnection(
             pika.ConnectionParameters(*self._args, **self._kwargs)) as c:
            channel = c.channel()
            channel.basic_publish(
                exchange=self._exchange,
                routing_key=self._routing_key,
                body=msg,
                properties=pika.BasicProperties(delivery_mode=2)
            )
