# coding: utf-8
import traceback
import pika
from constants import Ku


def init_session(url):
    parameters = pika.URLParameters(url)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    return connection, channel


def upload_data(channel, data, sport_type_id):
    try:
        exchange = Ku.Mapping.get_exchange_name(sport_type_id)
        channel.basic_publish(exchange='events', routing_key=exchange, body=memoryview(data.SerializeToString()))
    except Exception:
        traceback.print_exc()
        return False
    return True
