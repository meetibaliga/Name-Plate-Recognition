# Sample Flask REST server implementing two methods
##
# Endpoint /api/image is a POST method taking a body containing an image
# It returns a JSON document providing the 'width' and 'height' of the
# image that was provided. The Python Image Library (pillow) is used to
# proce#ss the image
##
# Endpoint /api/add/X/Y is a post or get method returns a JSON body
# containing the sum of 'X' and 'Y'. The body of the request is ignored
##
##
from flask import Flask, request, Response
import jsonpickle
import numpy as np
from PIL import Image
import io
import hashlib
import pika
import json
import base64
import redis
import socket
import time
app = Flask(__name__)

@app.route('/predict', methods=['PUT'])
def predict_and_put():
    r = request
    # convert the data to a PIL image type so we can extract dimensions
    try:
        data = json.loads(r.data)
        message = {'videoid': data['videoid']}

        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq')) #rabbitmq server
        channel = connection.channel()
        channel.exchange_declare(exchange='direct_exchange', exchange_type='direct')
        channel.exchange_declare(exchange='log_exchange', exchange_type='topic')
        channel.queue_declare(queue="toWorker")
        channel.basic_publish(exchange="direct_exchange", routing_key="video", body=json.dumps(message))
        connection.close()

        time.sleep(2)
        table1 = redis.StrictRedis(host='redis', port=6379, db=1)
        list_value = table1.get(data['videoid']).decode("utf-8")
        
        
        #print(type(list_value), list_value)
        org,pred,title = list_value.split(":")
        #print(type(org),type(pred), type(title))
        #print(org,pred,title)
        response = {
                'original_likes': org,
                'predicted_likes': pred,
                'title': title
        }
        

    except Exception as e:
        print(e)
        response = {'predicted_likes': 0}
    # encode response using jsonpickle
    response_pickled = jsonpickle.encode(response)

    return Response(response=response_pickled, status=200, mimetype="application/json")

app.run(host="0.0.0.0", port=5000)
