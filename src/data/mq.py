import json, time

import pika
from pika.exceptions import (
    AMQPChannelError,
    AMQPConnectionError,
    AuthenticationError,
    ChannelWrongStateError,
    StreamLostError,
)
import phpserialize3 as phpSerializer
import uuid_utils as uuid

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
        except AuthenticationError as auth_error:
            print(f"[AMQP_AUTHENTICATION]: Client auth failed. {auth_error}")
        except AMQPConnectionError:
            print(
                "[AMQP_CONNECTION_ERROR]: Please check server configurations. Connection error"
            )
        except AMQPChannelError:
            print("[AMQP_CHANNEL_ERROR]: Wrong Configurations. Fix RabbitMQ Channel.")
        except TimeoutError:
            print("[AMQP_TIMEOUT]: RabbitMQ connection timeout.")
        except StreamLostError:
            time.sleep(3)
            self.connect()
            print("[AMQP_STREAM_LOST]: Transport indicated EOF.")
        except Exception as e:
            print(f"Unknown error\n{e}")

    def close(self):
        """Close the RabbitMQ."""
        if self.connection and not self.connection.is_closed:
            self.connection.close()

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

        try:
            self.channel.queue_declare(queue=queue_name, durable=True)
            self.channel.queue_bind(
                exchange="system-logs",
                queue=queue_name,
                routing_key=routing_key,
            )
            self.channel.basic_publish(
                exchange="system-logs",
                routing_key=routing_key,
                body=json.dumps(message, indent=2).encode("utf-8"),
                properties=pika.BasicProperties(delivery_mode=2),
            )
            print(json.dumps(message, indent=2))
        except ChannelWrongStateError as channel_error:
            print(f"[BROKER]: {channel_error}")
        except TypeError as channel_blocking_error:
            print(f"[BROKER]: {channel_blocking_error}")

    def laravel_based_messaging(self, namespace: str, data: dict):
        """Laravel-based Messaging AMQP Format

        Args:
            namespace (str): Laravel MQ directory namespace
            data (dict): Main data to stream
        Return: Proper data streams that Laravel can support.
        """
        stream: dict = {
            "data": data,
            "connection": "rabbitmq",
            "queue": "logs",
        }

        command: str = phpSerializer.dumps(stream)

        return {
            "uuid": str(uuid.uuid4()),
            "displayName": namespace,
            "job": "Illuminate\\Queue\\CallQueuedHandler@call",
            "maxTries": None,
            "maxExceptions": None,
            "failOnTimeout": False,
            "backoff": None,
            "timeout": None,
            "retryUntil": None,
            "data": {
                "commandName": namespace,
                "command": f'O:{len(namespace)}:"{namespace}":'
                + str(len(stream))
                + ":{s:"
                + str(6 + len(namespace))
                + f':"\u0000{namespace}\u0000data";'
                + command[16:],
            },
            "id": str(uuid.uuid4()),
        }
