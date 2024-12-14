from pymongo import MongoClient
from pymongo.errors import (
    ConnectionError,
    ServerSelectionTimeoutError,
    ConfigurationError,
    InvalidOperation,
)

from config import config


class Controllers:
    def __init__(self, building: str, ip: str):
        self.building = building
        self.ip = ip

        try:
            self.connection_string = MongoClient(
                config["db"]["mongo"]["connection_string"],
                maxPoolSize=20,
                minPoolSize=5,
            )
            self.db_connection = self.connection_string.MCI_PCR_DB
        except ConnectionError:
            print("[MONGODB]: Mongodb connection error")
        except ServerSelectionTimeoutError:
            print("[MONGODB]: Server not available")
        except ConfigurationError:
            print("[MONGODB]: Config error")

    def get_floors(self) -> int:
        """Selects a gateway by IP address and get its floor"""

        try:
            gateway = self.db_connection.GateWay.find_one(
                {"building": self.building, "Status": 1, "ip": self.ip}
            )

            return gateway["floor"]
        except InvalidOperation:
            print("[MONGODB]: Invalid operation to find entered floor number.")
        except Exception as e:
            print(e)

        return 0

    def get_sensors(self):
        return self.db_connection.Slot.find(
            {
                "building": self.building,
                "floor": self.get_floors(),
            },
            sort=[("id", 1)],
        )

    def get_sensors_count(self):
        return self.db_connection.Slot.count_documents(
            {"building": self.building, "floor": self.get_floors()}
        )
