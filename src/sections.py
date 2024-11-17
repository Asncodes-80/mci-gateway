import socket, time

from pymongo import MongoClient

from config import config
from data import mq


class Building:
    name: str
    floor: int

    def __init__(self, name, floor):
        self.name = name
        self.floor = floor


class AppSections:
    ip: str
    port: int
    building: str
    message_queue = None
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

        self.connection_string = MongoClient("mongodb://localhost:27017/MCI_CPR_DB")
        self.conn = self.connection_string.MCI_CPR_DB
        self.message_queue = mq.RabbitMQ()

    # TODO: Remove the following method and create a class for MQ broker
    def sensor_status_update(
        self,
        status: str,
        sensor_id: str,
        building: Building,
    ):
        """Updating slot in the database (Rabbit is Here).

        Args:
            status (str): `0` for no car and `1` for occupied.
            sensor_id (str): Finds sensor by id to change its `real_status`.
            building (Building): Building information.
        """
        # conn.Slot.update_many(
        #     {
        #         "id": sensor_id,
        #         "floor": building.floor,
        #         "building": building.name,
        #     },
        #     {"$set": {"real_status": status}},
        # )
        self.message_queue.produce(
            self.queue_name,
            self.queue_route,
            message={
                "id": sensor_id,
                "status": status,
                "address": self.ip,
            },
        )
        self.message_queue.close()

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
                            self.sensor_status_update(
                                0,
                                str(response[:2]),
                                Building(self.building_name, floor),
                            )
                        elif response[12:14] == "01":  # Slot is occupied
                            self.sensor_status_update(
                                1,
                                str(response[:2]),
                                Building(self.building_name, floor),
                            )
                        time.sleep(0.8)
                    # To prevent if a sensor was freezed
                    except socket.timeout:
                        print("TimeOut: Next Sensor")
                        continue
                client.close()
            except socket.timeout:
                print("Socket timeout")
