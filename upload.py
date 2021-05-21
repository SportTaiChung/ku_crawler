# coding: utf-8
import traceback
import pika


def init_session(url):
    parameters = pika.URLParameters(url)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    return connection, channel


def upload_data(channel, data):
    try:
        channel.basic_publish(exchange='test_QA', routing_key='', body=data.SerializeToString())
    except Exception as ex:
        traceback.print_exc()
