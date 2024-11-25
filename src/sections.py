import socket, time

from pymongo import MongoClient
import uuid_utils as uuid
from phpserialize3 import *

from config import config
from data import mq


class AppSections:
    ip: str
    port: int
    building: str
    message_broker = None
    queue_name: str
    queue_route: str
    connection_string = None
    conn = None

    def __init__(
        self,
        ip,
        port,
        building,
    ):
        self.ip = ip
        self.port = port
        self.building = building

        self.connection_string = MongoClient("mongodb://localhost:27017/MCI_PCR_DB")
        self.conn = self.connection_string.MCI_PCR_DB
        self.message_broker = mq.RabbitMQ()

    def sensor_status_update(
        self,
        status: bool,
        sensor_id: str,
    ):
        """Updating slot in the database (Rabbit is Here).

        Args:
            status (str): `0` for no car and `1` for occupied.
            sensor_id (str): Finds sensor by id to change its `real_status`.
        """
        JOB_NAMESPACE: str = "App\\Jobs\\UltrasonicSensors\\SensorLog"

        cmd = (
            {
                "__PHP_Incomplete_Class_Name": JOB_NAMESPACE,
                "data": {
                    "sensor_id": sensor_id,
                    "status": status,
                    "ip_address": self.ip,
                    "message": "",
                },
                "connection": "rabbitmq",
                "queue": "logs",
            },
        )

        data: dict = {
            "uuid": str(uuid.uuid4()),
            "displayName": JOB_NAMESPACE,
            "job": "Illuminate\\Queue\\CallQueuedHandler@call",
            "maxTries": None,
            "maxExceptions": None,
            "failOnTimeout": False,
            "backoff": None,
            "timeout": None,
            "retryUntil": None,
            "data": {
                "commandName": JOB_NAMESPACE,
                "command": 'O:36:"App\\Jobs\\UltrasonicSensors\\SensorLog":3:{s:42:"\u0000App\\Jobs\\UltrasonicSensors\\SensorLog\u0000data";a:2:{s:9:"sensor_id";i:123;s:6:"status";b:1;}s:10:"connection";s:8:"rabbitmq";s:5:"queue";s:4:"logs";}',
            },
            "id": str(uuid.uuid4()),
        }

        self.message_broker.produce(
            self.queue_name,
            self.queue_route,
            message=data,
        )

    def sensor_data_collector(self):
        """Sensor Data Collection

        # Args:
            building (str):
            hostname (undefined):
            port (undefined):

        # Descriptions:

        This script sends request to network socket server and request format is
        compound of `sensor_id` and default read sensor command.

        After script got client response form gateway board, at slice of 12:14 we
        specify that slot is free or occupied.
        + 12:14 was equal to `00`: free
        + 12:14 was equal to `01`: occupied

        ## Message Queue Manager

        There are two topics of RabbitMQ:
        + `service_monitoring`: For Optimization and Monitoring (O&M) app
        + `application`: For client app
        """
        while True:
            try:
                client: socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.connect((self.ip, self.port))
                client.settimeout(2)
                gateway = self.conn.GateWay.find_one(
                    {"building": self.building, "Status": 1, "ip": self.ip}
                )
                # Select a gateway by ip address and get its floor
                floor: int = gateway["floor"]
                # Sensors list that exists in a specific floor
                sensors = self.conn.Slot.find(
                    {"building": self.building, "floor": floor}, sort=[("id", 1)]
                )
                sensors_count = self.conn.Slot.count_documents(
                    {"building": self.building, "floor": floor}
                )

                for _ in range(sensors_count):
                    sensor_id: str = sensors.next()["id"]
                    # Sensor read command in HEX format
                    client.send(
                        f"{sensor_id}{config["client_commands"]["sensor_read"]}".encode()
                    )
                    try:
                        response: str = client.recv(1024).hex()
                        if response[12:14] == "00":  # Slot is free
                            self.sensor_status_update(False, str(response[:2]))
                        elif response[12:14] == "01":  # Slot is occupied
                            self.sensor_status_update(True, str(response[:2]))
                        time.sleep(0.8)
                    # To prevent if a sensor was freezed
                    except Exception as db_except:
                        print(db_except)
                        print(f"MongoDB Exception\n{db_except}")
                        continue
                client.close()
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
