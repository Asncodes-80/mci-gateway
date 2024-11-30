import socket, time

from pymongo import MongoClient

from config import config
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

    def sensor_status_update(
        self,
        status: bool,
        sensor_id: str,
    ):
        """Update Slot in the Database.

        Args:
            status (bool): `False` for unavailable car and `True` for occupied.
            sensor_id (str): Finds sensor by id to change its `real_status`.
        """

        self.message_broker.produce(
            self.queue_name,
            self.queue_route,
            message=self.message_broker.laravel_based_messaging(
                namespace=self.queue_namespace_provider,
                data={
                    "sensor_id": sensor_id,
                    "status": status,
                    "ip_address": self.ip,
                },
            ),
        )

    def data_collector(self, callback=None):
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

    def sensors(self, client: socket):
        """Sensor Data Collection

        # Args:
            client (socket):

        # Descriptions:

        This script sends request to network socket server and request format is
        compound of `sensor_id` and default read sensor command.

        After script got client response form gateway board, at slice of 12:14
        we specify that slot is free or occupied:

        + 12:14 was equal to `00`: free
        + 12:14 was equal to `01`: occupied

        ## Message Queue Manager

        There are two topics of RabbitMQ:

        + `service_monitoring`: For Optimization and Monitoring (O&M) app
        + `application`: For client app
        """
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
            # Sensor's read command in HEX format
            client.send(
                f"{sensor_id}{config["client_commands"]["sensor_read"]}".encode()
            )
            try:
                response: str = client.recv(1024).hex()

                # Slot is free
                if response[12:14] == "00":
                    self.sensor_status_update(False, response[:2])
                # Slot is occupied
                elif response[12:14] == "01":
                    self.sensor_status_update(True, response[:2])

                time.sleep(0.8)
            except Exception as db_exception:
                print(db_exception)
                continue
        client.close()
