from data import mq

mq = mq.RabbitMQ()
message = {
    "sensor": "01",
    "status": "1",
}
mq.produce(queue_name="topic_1", message=message)
print(f"Sending {message}")
mq.close()
