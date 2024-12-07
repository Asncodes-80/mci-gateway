import socket, time

from pymongo import MongoClient

from config import config, Log
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
        result = {
            "ip_address": self.ip,
        }

        for k, v in data.items():
            result[k] = v

        self.message_broker.produce(
            self.queue_name,
            self.queue_route,
            message=self.message_broker.laravel_based_messaging(
                namespace=self.queue_namespace_provider,
                data=result,
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

        After script got client response form gateway board, at slice of `12:14`
        we specify that slot is free or occupied:

        + 12:14 was equal to `00`: free
        + 12:14 was equal to `01`: occupied
        + 0:2 was equal to `00`: sensor is disconnected
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

                # Sensor is not connect
                if response[0:2] == "00":
                    self.send_event(
                        data={
                            "sensor_id": sensor_id,
                            "message": {
                                "level": Log.warning.name,
                                "content": None,
                            },
                        }
                    )
                else:
                    # Slot is free
                    if response[12:14] == "00":
                        self.send_event(
                            data={
                                "sensor_id": sensor_id,
                                "status": False,
                                "message": None,
                            }
                        )
                    # Slot is occupied
                    elif response[12:14] == "01":
                        self.send_event(
                            data={
                                "sensor_id": sensor_id,
                                "status": True,
                                "message": None,
                            }
                        )

                time.sleep(0.8)
            except Exception as db_exception:
                print(f"[MONGODB]: {db_exception}")
                continue
        client.close()
