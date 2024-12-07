""" Sensor Data Collector Python App Documentations 

+ Every `id` key is related to (str) `sensor_id`
+ (int) `real_status` is related to status of specific sensor -> `sensor_id`.

## Server Side Log Table

+ info: Every data that we send over MQ
+ waning: Minor events like some clients is disconnected.
+ error: Major events like a part of section encounter to fault.
+ critical: Critical events like any inside communications.

## Server-side Logs

| Type              | Case                                             |
|-------------------|--------------------------------------------------|
| info              | RabbitMQ successful connection                   |
| info              | Redis successful connection                      |
| info              | Section is working                               |
| warning           | Sensor disconnection                             |
| critical          | Global client socket timeout                     |
| critical          | Redis connection error                           |

## Application-side Log Table

| Type             | Group                  | Description                                                                 |
|------------------|------------------------|-----------------------------------------------------------------------------|
| NoneType         | Network                | Network is Unreachable                                                      |
| NoneType         | Implementation         | Object is not subscriptable                                                 |
| Timeout          | RabbitMQ               | RabbitMQ connection timeout                                                 |
| Timeout          | Socket                 | [Error 104] Connection reset by peer                                        |
| CLI Input        | User mode              | Unknown section                                                             |
| CLI Input        | User mode              | You must enter building number between 1 to {len(config["buildings"])}"     |
| Connection Error | Service mode           | [AMQPConnectionError]: Please check server configurations. Connection error |
| Connection Error | Service mode           | [AMQPChannelError]: Wrong Configurations. Fix RabbitMQ Channel.             |
| Connection Error | Service mode           | RabbitMQ Connection Error                                                   |
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

        if args.ip == None or args.port == None or args.section == None:
            print(
                "[INPUT]: Please enter valid ip address, port number, and an application section"
            )
        else:
            print("Enter building name from the following list:")

            for index, building_name in enumerate(config["buildings"]):
                print(f"{index + 1}) {building_name}")

            building: int = int(input("Building name: "))

            if building < 0 or building > len(config["buildings"]):
                print(
                    f"[INPUT]: You must enter building number between 1 to {len(config["buildings"])}"
                )
            else:
                # Initialized application with proper section, port, and ip
                # address.
                app_section = AppSections(
                    args.ip,
                    int(args.port),
                    config["buildings"][building - 1],
                    queue_name="logs",
                )

                match args.section:
                    case "sensors":
                        app_section.queue_route = "logs.utlrasonic-sensors"
                        app_section.queue_namespace_provider = (
                            "App\\Jobs\\SystemLogs\\UltrasonicSensors\\SensorLog"
                        )

                        app_section.data_collector(app_section.sensors)
                    case "barrier":
                        # TODO:
                        print("Performing barrier application section.")
                    case "rfid":
                        # TODO:
                        print("Performing rfid application section.")
                    case _:
                        print("[INPUT]: Unknown section")
    except KeyboardInterrupt:
        # Close the broker with specific `exchange` and `queue_name`.
        app_section.message_broker.close()
        sys.exit(0)
