import json

import pika
from pika.exceptions import AMQPChannelError, AMQPConnectionError, AMQPError

from config import config


class RabbitMQ:
    def __init__(self):
        self.user = config["mq"]["user"]
        self.password = config["mq"]["password"]
        self.host = config["mq"]["host"]
        self.port = config["mq"]["port"]
        self.connection = None
        self.channel = None
        self.connect()

    def connect(self):
        """Open the RabbitMQ Connection."""
        try:
            credentials = pika.PlainCredentials(self.user, self.password)
            parameters = pika.ConnectionParameters(
                host=self.host, port=self.port, credentials=credentials
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
        except AMQPConnectionError:
            print(
                "[AMQPConnectionError]: Please check server configurations. Connection error"
            )
        except AMQPChannelError:
            print("[AMQPChannelError]: Wrong Configurations. Fix RabbitMQ Channel.")
        except TimeoutError:
            print("[Timeout]: RabbitMQ connection timeout")
        except Exception as e:
            print(f"Unknown error\n{e}")

    def close(self):
        """Close the RabbitMQ."""
        if self.connection and not self.connection.is_closed:
            self.connection.close()

    def consume(self, queue_name: str, callback):
        """Consume and Listen for Latest Data.

        Args:
            queue_name (str): Topic name
            callback (function): Stream response

        Raises:
            Exception: Connect error.
        """
        if not self.channel:
            raise Exception("Connection is not established!")

        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=callback,
            auto_ack=True,
        )
        self.channel.start_consuming()

    def produce(self, queue_name: str, routing_key: str, message: dict):
        """Produce and Publish Data to Streamline.

        Args:
            queue_name (str): Topic name
            routing_key (str): Defines route of logs
            message (dict): main context

        Raises:
            Exception: Connection error.
        """
        if not self.channel:
            raise Exception("Connection is not established!")

        self.channel.queue_declare(queue=queue_name, durable=True)
        self.channel.basic_publish(
            exchange="",
            routing_key=routing_key,
            body=json.dumps(message, indent=2).encode("utf-8"),
            properties=pika.BasicProperties(delivery_mode=2),
        )
        print(f"Send message to queue {queue_name}: {message}")
