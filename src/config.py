config: dict = {
    "client_commands": {
        "sensor_read": "03000A0005",
        "barrier": {
            "read": "",
            "open": "",
        },
    },
    "sections": [
        "sensors",
        "barriers",
        "rfid",
    ],
    "buildings": [
        "vanak",
        "huawei",
        "setareh",
    ],
    "options": {
        "--ip": "-i",
        "--port": "-p",
        "--section": "-s",
    },
    "mq": {
        "user": "admin",
        "password": "admin",
        "host": "localhost",
        "port": 5672,
    },
}
