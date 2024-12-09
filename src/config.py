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
        "user": "message_broker",
        "password": "1234",
        "host": "127.0.0.1",
        "port": 5672,
    },
    "db": {
        "mongo": {
            "connection_string": "mongodb://localhost:27017/MCI_PCR_DB",
        },
        "redis": {},
    },
}
