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
        # channel.basic_publish(exchange='KU', routing_key=exchange, body=data.SerializeToString())
        channel.basic_publish(exchange=exchange, routing_key='', body=data.SerializeToString())
    except Exception as ex:
        traceback.print_exc()
