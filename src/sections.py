import json, socket, time

from pymongo import MongoClient

from config import config
from data.models import error_code, Log, AMQPLoggingMessage, SensorsLogging
from data.controllers import Controllers
from data import mq


class AppSections:
    connection_string: str
    conn: str
    message_broker: any = None
    queue_route: str = ""
    queue_namespace_provider: str = ""

    def __init__(self, ip: str, port: int, building: str, queue_name: str):
        self.ip = ip
        self.port = port
        self.building = building
        self.queue_name = queue_name
        self.connection_string = MongoClient(config["db"]["mongo"]["connection_string"])
        self.conn = self.connection_string.MCI_PCR_DB
        self.message_broker = mq.RabbitMQ()

    def send_event(self, data: dict):
        """Send proper event by payload to RabbitMQ.

        Args:
            data (dict): The simple dictionary includes the client IP address
            and other related data.
        """

        # Final data to send it to RabbitMQ
        results = {"ip_address": self.ip}

        # Updates `results` from new data dictionary.
        for k, v in data.items():
            results[k] = v

        self.message_broker.produce(
            self.queue_name,
            self.queue_route,
            message=self.message_broker.laravel_based_messaging(
                namespace=self.queue_namespace_provider,
                data=results,
            ),
        )

    def socket_connection(self, callback=None):
        """Public Data Collector

        Args:
            callback (client: socket): Call `sensors`, `barriers`, `rfids` and
            other client's function here.
        """
        while True:
            try:
                client: socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.connect((self.ip, self.port))
                client.settimeout(2)

                if callback:
                    callback(client)
                else:
                    raise Exception("[CODE]: Error in callback function.")

            except socket.error:
                print("[SOCKET]: Access is closed.")
            except socket.gaierror:
                print("[SOCKET]: DNS is not exists.")
            except ConnectionAbortedError:
                print("[SOCKET]: The Connection is terminated by one of the parties.")
            except ConnectionRefusedError:
                print("[SOCKET]: The Connection refused.")
            except ConnectionResetError:
                print("[SOCKET]: The Connection closed with another gateway.")
            except socket.timeout:
                print("[SOCKET]: Connection timeout")
            except OSError as os_conn_error:
                print(f"[CONNECTION]: Gateway is not responding. {os_conn_error}")

    def get_sensors_data(self, client: socket):
        """Get Sensors Data

        # Args:
            client (socket):

        # Descriptions:

        This script sends request to network socket server and request format is
        compound of `sensor_id` and default read sensor command.

        After script got client response form gateway board, at slice of `12:14`
        we specify that slot is free or occupied:

        + 12:14 was equal to `00`: free
        + 12:14 was equal to `01`: occupied
        + 0:2 was equal to `00`: sensor is disconnected
        """
        # Database controllers
        sensor_collections = Controllers(self.conn, self.building, self.ip)

        # Sensors list that exists in a specific floor
        sensors = sensor_collections.get_sensors()

        for _ in range(sensor_collections.get_sensors_count()):
            sensor_id: str = sensors.next()["id"]
            # Sensor's read command in HEX format
            client.send(
                f"{sensor_id}{config["client_commands"]["sensor_read"]}".encode()
            )
            try:
                sensor_response: str = client.recv(1024).hex()

                # Initialize `sensor_logging`
                sensor_logging: SensorsLogging = SensorsLogging(sensor_id, None, None)

                # Sensor is not connect
                if sensor_response[0:2] == "00":
                    sensor_logging.message = (
                        AMQPLoggingMessage(
                            level=Log.warning.name,
                            content=error_code["sections"]["warning"][
                                "sensorIsDisconnected"
                            ],
                        ),
                    )
                    self.send_event(data=json.dumps(sensor_logging))
                else:
                    # Slot is free
                    if sensor_response[12:14] == "00":
                        sensor_logging.status = False
                        sensor_logging.message = (
                            AMQPLoggingMessage(
                                level=Log.info.name,
                                content=error_code["sections"]["success"][
                                    "globalStatus"
                                ],
                            ),
                        )
                        self.send_event(data=json.dumps(sensor_logging))
                    # Slot is occupied
                    elif sensor_response[12:14] == "01":
                        sensor_logging.status = True
                        sensor_logging.message = (
                            AMQPLoggingMessage(
                                level=Log.info.name,
                                content=error_code["sections"]["success"][
                                    "globalStatus"
                                ],
                            ),
                        )
                        self.send_event(data=json.dumps(sensor_logging))

                time.sleep(0.8)
            except Exception as db_exception:
                print(f"[MONGODB]: {db_exception}")
                continue
        client.close()
