import os

from ..core import DriverBase, format_msg
import pika


class Driver(DriverBase):
    def __init__(self, exchange, queue, routing_key=None, *args, **kwargs):
        super().__init__()
        self._exchange = exchange
        self._routing_key = routing_key or queue
        self._conn = pika.BlockingConnection(
            pika.ConnectionParameters(*args, **kwargs))
        self._chan = self._conn.channel()
        self._chan.exchange_declare(exchange=exchange, durable=True)
        self._chan.queue_declare(queue=queue, durable=True)
        self._chan.queue_bind(
            exchange=exchange,
            queue=queue,
            routing_key=self._routing_key
        )

    def close(self):
        self._conn.close()
        super().close()

    def run(self, driver_id, ts, fields, tags):
        if not fields:
            return
        msg = format_msg(ts, driver_id, tags, fields)
        self._chan.basic_publish(
            exchange=self._exchange,
            routing_key=self._routing_key,
            body=msg,
            properties=pika.BasicProperties(delivery_mode=2)
        )
