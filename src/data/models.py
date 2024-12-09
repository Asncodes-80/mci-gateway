from enum import Enum
from dataclasses import dataclass


class Log(Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


@dataclass
class AMQPLoggingMessage:
    level: str
    content: int


@dataclass
class SensorsLogging:
    sensor_id: str
    status: bool
    message: AMQPLoggingMessage


error_code: dict[str, dict[str, int]] = {
    "connected": {
        "rabbit": 1101,
        "redis": 1201,
    },
    "disconnected": {
        "rabbit": 4100,
        "redis": 4200,
    },
    "sections": {
        "success": {
            "globalStatus": 1301,
        },
        "warning": {
            "sensorsIsDisconnected": 2300,
        },
        "critical": {
            "socketTimeout": 4300,
        },
    },
}
