""" Sensor Data Collector Python App Documentations 

+ Every `id` key is related to (str) `sensor_id`
+ (int) `real_status` is related to status of specific sensor -> `sensor_id`.

# Log Table

| Type     | Group            | Description                         |
|----------|------------------|-------------------------------------|
| NoneType |   Network        | Network is Unreachable              |
| NoneType |   Implementation | Object is not subscriptable         |
| Timeout  |   Exception      | [Error 104] Connection reset by peer|
"""

import argparse, sys

from config import config
from sections import AppSections


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(
            prog="MCI Smart Parking Gateway Service Script",
            description="With this service you can find every slots sensors, barriers, and RFID server only with IP address and port number",
            epilog=f"""
            Don't forget use these buildings name for your input:
            {config["buildings"]}
            """,
        )
        for key, value in config["options"].items():
            parser.add_argument(value, key)
        args = parser.parse_args()

        print("Enter building name from the following list:")
        for index, building_name in enumerate(config["buildings"]):
            print(f"{index + 1}) {building_name}")
        building: str = input("Building name: ")

        if (
            building == None
            or args.ip == None
            or args.port == None
            or args.section == None
            or building_name == ""
        ):
            print(
                "Bad input!\nPlease enter valid ip address, port number, application section, and a specific building name"
            )
        else:
            app_section = AppSections(args.ip, args.port, building)
            match args.section:
                case "sensors":
                    app_section.queue_name = "system-logs"
                    app_section.queue_route = "ultra_sonic"
                    app_section.sensor_data_collector()
                case "barriers":
                    print("Performing barriers application section")
                case "rfid":
                    print("Performing rfid application section")
    except KeyboardInterrupt:
        sys.exit(0)
