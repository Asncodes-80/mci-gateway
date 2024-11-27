import json, sys

import pika
from pika.exceptions import (
    AMQPChannelError,
    AMQPConnectionError,
    AuthenticationError,
    ChannelWrongStateError,
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
            print(f"[AMQPAUTHENTICATION]: Client auth failed. {auth_error}")
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
        finally:
            sys.exit(0)

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
            json.dumps(message, indent=2)
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
        command: str = phpSerializer.dumps(
            {
                "data": data,
                "connection": "rabbitmq",
                "queue": "logs",
            }
        )
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
                "command": 'O:36:"{ns}":3:{s:42:"\u0000{ns}\u0000data";'.format(
                    ns=namespace
                )
                + command[16:],
            },
            "id": str(uuid.uuid4()),
        }
