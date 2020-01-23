import re
import sklearn
import pika
import json
import base64
import redis
import pandas as pd
import numpy as np
import pickle
import requests
import random
import time
import math
import sys
import socket

API_KEYS = ["AIzaSyCGqRW3JvEhx0fDe83JkQWysC7OZNn99Mo"]

cache = redis.Redis(host='redis', port='6379', db=1)

connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
channel = connection.channel()
channel.exchange_declare(exchange='direct_exchange', exchange_type='direct')
result = channel.queue_declare(queue='toWorker')
queue_name = result.method.queue
channel.queue_bind(exchange='direct_exchange', queue=queue_name, routing_key='video')

#to send to rabbit
channel.exchange_declare(exchange='log_exchange', exchange_type='topic')

data={"V_id":"","commentCount":"","dislikeCount":"","likeCount":"","viewCount":"","publishedAt":"", "title":""}

def send_info_message(message_string):
    message = {'message_string' : message_string}
    routing_key = socket.gethostname()+".info"
    channel.basic_publish(exchange="log_exchange", routing_key=routing_key, body=json.dumps(message))

#send debug logs
def send_debug_message(message_string):
    message = {'message_string' : message_string}
    routing_key = socket.gethostname()+".debug"
    channel.basic_publish(exchange="log_exchange", routing_key=routing_key, body=json.dumps(message))

# The function returns the final URL for request
def get_url(Video_urls):
    v_id =  Video_urls
    API_KEY = API_KEYS[0]
    url = "https://www.googleapis.com/youtube/v3/videos?part=status,snippet,topicDetails,contentDetails,statistics&id="+v_id+"&key="+API_KEY
    return url

# This function populates the data dictionary
def add_data(i,key1,key2,key3="NA"):
    if key3!="NA":
        try:
            data[key1] = i[key2][key3]
        except Exception,err:
            if key1 in ['viewCount', 'commentCount','dislikeCount','publishedAt','title']:
                print i["id"]
                print key1+"missing"
            data[key1] = 0
    else:
        try:
            data[key1] = i[key2]
            #data[key1].append(i[key2])
        except:
            data[key1]= None

# The function is used to get the Video relevant data
def video_data(get_json):
    for i in get_json["items"]:

# -----------------------------------VIDEO RELATED FEATURES   ---------------------------------------------------------------------

        add_data(i,key1="V_id",key2='id')
        add_data(i,key1="commentCount",key2="statistics",key3="commentCount")
        add_data(i,key1="dislikeCount",key2="statistics",key3="dislikeCount")
        add_data(i,key1="likeCount",key2="statistics",key3="likeCount")
        add_data(i,key1="viewCount",key2="statistics",key3="viewCount")
        add_data(i,key1="publishedAt",key2="snippet",key3="publishedAt")
        add_data(i,key1="title",key2="snippet",key3="title")

def get_months(x):
        return 12-x.month+(2019-(x.year))*12

# The function gets the data after coverting to derived features
def get_final_data(df):

    df["months_old"] = pd.to_datetime(df.publishedAt).apply(lambda x: get_months(x))
    df["viewCount/video_month_old"] = df.apply(lambda x: float(x["viewCount"]) / float(x["months_old"]),axis=1)

    return df

def insert_into_redis(V_id, org, pred, title):

    title = re.findall(r'\w+',title[0])
    title = ' '.join(title)
    print(title)
    value = str(int(org[0]))+":"+str(int(pred[0]))+":"+title
    send_info_message("Inserting into table:"+V_id[0]+","+value)
    cache.set(V_id, value)
    send_debug_message("Push Successful")

def predict_likes(V_id):
    url = get_url(V_id)
    send_debug_message("Url: "+url)

    r = requests.get(url)
    get_json = r.json()
    video_data(get_json)
    #print data
    df = pd.DataFrame(data,index=[0])
    #print df
    df = get_final_data(df)
    #print df
    features = ['viewCount','commentCount', 'dislikeCount','viewCount/video_month_old']

    X_test = df[features]
    Y_test = df["likeCount"]

    filename = "model-final"
    fileObject = open(filename,'r')
    model = pickle.load(fileObject)
    clf = model


    np.set_printoptions(suppress=True)
    pred  = np.ceil(clf.predict(X_test))
    org = np.array(Y_test).astype("float32")
    err = ((pred-org)/org)*100.0
    V_id = data["V_id"]
    diff = pred - org

    try:
        out = pd.DataFrame({"V_ids":V_id,"Original":org,"Predicted":pred,"Difference(+/-)":diff})
        send_info_message("Video_Id: "+V_id[0]+" Original Likes: "+str(int(org[0]))+" Predicted Likes: "+str(int(pred[0]))+" Difference: "+str(int(diff[0])))
        insert_into_redis(V_id, org, pred, df["title"])
    except Exception as E:
        send_debug_message(E)

def callback(ch, method, properties, body):
    send_info_message("Recevied toWorker Message..")
    
    datastore = json.loads(body)
    V_id = datastore["videoid"]
    send_info_message("VideoID Received: "+V_id)
    try:
        predict_likes(V_id)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as E:
        print(E)
        #send_debug_message(E)
        ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue_name, callback)
channel.start_consuming()
