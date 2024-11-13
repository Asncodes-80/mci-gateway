from data import mq


def callback(ch, method, properties, body):
    print(f"Data: {body}")


mq = mq.RabbitMQ()
mq.consume(queue_name="topic_1", callback=callback)
