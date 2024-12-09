from enum import Enum


class Log(Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


class AMQPLoggingMessage:
    def __init__(self, level: Log, content: int):
        """AMQP Logging Message Structure

        Keyword arguments:
        level (string):
        """
        self.level = level
        self.content = content


class SensorsLogging:
    def __init__(
        self,
        sensor_id: str,
        status: bool,
        message: AMQPLoggingMessage,
    ):
        self.sensor_id = sensor_id
        self.message = message
        self.status = status


"""Server-side Logs

| Code | Type              | Case                              |
|------|-------------------|-----------------------------------|
| 1101 | info              | RabbitMQ successful connection    |
| 1201 | info              | Redis successful connection       |
| 1301 | info              | Section is working                |
| 2300 | warning           | Sensor disconnection              |
| 4300 | critical          | Global client socket timeout      |
| 4000 | critical          | Redis connection error            |
"""
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
