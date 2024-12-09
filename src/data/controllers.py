class Controllers:
    def __init__(self, db_connection, building: str, ip: str):
        self.db_connection = db_connection
        self.building = building
        self.ip = ip

    def get_floors(self) -> int:
        """Selects a gateway by IP address and get its floor"""

        gateway = self.db_connection.GateWay.find_one(
            {"building": self.building, "Status": 1, "ip": self.ip}
        )

        return gateway["floor"]

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