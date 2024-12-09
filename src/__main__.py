""" Sensor Data Collector Python App Documentations

+ Every `id` key is related to (str) `sensor_id`
+ (int) `real_status` is related to status of specific sensor -> `sensor_id`.

## Server Side Log Table

+ **info**: Every data that we send over MQ -> 1XXX
+ **warning**: Minor events like some clients is disconnected -> 2XXX
+ **error**: Major events like a part of section encounter to fault -> 3XXX
+ **critical**: Critical events like any inside communications -> 4XXX


## Application-side Log Table

| Error                 | Description                                                            |
|-----------------------|------------------------------------------------------------------------|
| INPUT                 | Please enter valid ip address, port number, and an application section |
| INPUT                 | You must enter building number between 1 to n                          |
| INPUT                 | Unknown section                                                        |
| CODE                  | `sections.socket_connection`: Error in callback function.              |
| SOCKET                | Access is closed.                                                      |
| SOCKET                | DNS is not exists.                                                     |
| SOCKET                | The Connection is terminated by one of the parties.                    |
| SOCKET                | The Connection refused.                                                |
| SOCKET                | The Connection closed with another gateway.                            |
| SOCKET                | Connection timeout.                                                    |
| CONNECTION            | Gateway is not responding.                                             |
| SOCKET                | The Connection refused.                                                |
| AMQP_AUTHENTICATION   | Client auth failed.                                                    |
| AMQP_CONNECTION_ERROR | Please check server configurations. Connection error                   |
| AMQP_CHANNEL_ERROR    | Wrong Configurations. Fix RabbitMQ Channel.                            |
| AMQP_TIMEOUT          | RabbitMQ connection timeout.                                           |
| BROKER                | Channel error {dynamic error}                                          |
| BROKER                | {channel blocking error}                                               |


## Server-side Logs

| Code | Type              | Case                              |
|------|-------------------|-----------------------------------|
| 1101 | info              | RabbitMQ successful connection    |
| 1201 | info              | Redis successful connection       |
| 1301 | info              | Section is working                |
| 2300 | warning           | Sensor disconnection              |
| 4300 | critical          | Global client socket timeout      |
| 4000 | critical          | Redis connection error            |
"""

import argparse, sys

from config import config
from sections import AppSections


if __name__ == "__main__":
    app_section: AppSections
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

                        app_section.socket_connection(app_section.get_sensors_data)
                    case "barrier":
                        # TODO:
                        print("Performing barrier application section.")
                    case "rfid":
                        app_section.queue_route = "logs.rfids"
                        app_section.queue_namespace_provider = (
                            "App\\Jobs\\SystemLogs\\RFIDs\\RFIDLog"
                        )
                        print("Performing rfid application section.")
                    case _:
                        print("[INPUT]: Unknown section")
    except KeyboardInterrupt:
        # Close the broker with specific `exchange` and `queue_name`.
        app_section.message_broker.close()
        sys.exit(0)
